import os
from datetime import timedelta

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test-unused.db")

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app
from app.models.user import User

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(test_engine)


def override_get_db() -> Iterator[Session]:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_database() -> Iterator[None]:
    yield
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def db_session() -> Iterator[Session]:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Resident",
            "email": "resident@example.com",
            "password": "secure-password-123",
        },
    )
    assert response.status_code == 201
    return response.json()


def register_and_login(
    client: TestClient,
    *,
    name: str,
    email: str,
    password: str = "password-123",
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert response.status_code == 201, response.text

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text

    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def make_admin(client: TestClient, email: str = "admin@example.com") -> dict:
    headers = register_and_login(client, name="Admin User", email=email)
    db = next(override_get_db())
    try:
        user = db.scalar(select(User).where(User.email == email))
        user.role = "admin"
        db.commit()
    finally:
        db.close()
    return headers


def seed_complaint(
    owner_email: str,
    category: str = "PLUMBING",
    description: str = "seeded",
) -> int:
    from app.services import complaint_service

    db = next(override_get_db())
    try:
        user = db.scalar(select(User).where(User.email == owner_email))
        complaint = complaint_service.create_complaint(
            db,
            resident=user,
            category=category,
            description=description,
        )
        return complaint.id
    finally:
        db.close()


def force_state(
    complaint_id: int,
    *,
    status: str | None = None,
    priority: str | None = None,
    age_days: float | None = None,
) -> None:
    from app.db.database import utcnow
    from app.models.complaint import Complaint

    db = next(override_get_db())
    try:
        complaint = db.get(Complaint, complaint_id)
        if status is not None:
            complaint.status = status
            complaint.resolved_at = utcnow() if status == "RESOLVED" else None
        if priority is not None:
            complaint.priority = priority
        if age_days is not None:
            complaint.created_at = utcnow() - timedelta(days=age_days)
        db.commit()
    finally:
        db.close()

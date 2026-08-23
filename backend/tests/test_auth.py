import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.dependencies import require_admin
from app.models.user import User
from tests.conftest import override_get_db


def test_register_success(client: TestClient, registered_user: dict) -> None:
    assert registered_user["id"] > 0
    assert registered_user["name"] == "Test Resident"
    assert registered_user["email"] == "resident@example.com"
    assert registered_user["role"] == "resident"
    assert "password_hash" not in registered_user
    assert "password" not in registered_user


def test_register_duplicate_email_returns_409(
    client: TestClient, registered_user: dict
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Another Person",
            "email": "resident@example.com",
            "password": "another-password-123",
        },
    )
    assert response.status_code == 409


def test_register_duplicate_email_case_insensitive_409(
    client: TestClient, registered_user: dict
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Case Tester",
            "email": "  RESIDENT@Example.COM ",
            "password": "case-insensitive-1",
        },
    )
    assert response.status_code == 409


def test_login_success_returns_token(client: TestClient, registered_user: dict) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "resident@example.com",
            "password": "secure-password-123",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20
    assert "." in body["access_token"]


def test_login_wrong_password_returns_401(
    client: TestClient, registered_user: dict
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "resident@example.com",
            "password": "wrong-password-999",
        },
    )
    assert response.status_code == 401


def test_login_unknown_email_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "ghost@example.com",
            "password": "whatever-password-1",
        },
    )
    assert response.status_code == 401


def test_me_with_valid_token(client: TestClient, registered_user: dict) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "resident@example.com", "password": "secure-password-123"},
    )
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    me = response.json()
    assert me["id"] == registered_user["id"]
    assert me["email"] == "resident@example.com"
    assert me["role"] == "resident"
    assert "password_hash" not in me


def test_me_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_garbage_token_returns_401(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.jwt"},
    )
    assert response.status_code == 401


def test_resident_cannot_pass_require_admin() -> None:
    resident = User(id=1, name="R", email="r@example.com", role="resident")
    with pytest.raises(HTTPException) as exc_info:
        require_admin(resident)
    assert exc_info.value.status_code == 403


def test_admin_passes_require_admin() -> None:
    admin = User(id=2, name="A", email="a@example.com", role="admin")
    assert require_admin(admin) is admin


def test_password_stored_as_hash_not_plaintext(
    client: TestClient, registered_user: dict
) -> None:
    from app.core.security import verify_password
    from tests.conftest import override_get_db

    db = next(override_get_db())
    try:
        user = db.get(User, registered_user["id"])
        assert user is not None
        stored_hash = user.password_hash

        assert stored_hash != "secure-password-123"
        assert "secure-password-123" not in stored_hash
        assert stored_hash.startswith("$argon2")

        assert verify_password("secure-password-123", stored_hash)
        assert not verify_password("wrong", stored_hash)
    finally:
        db.close()

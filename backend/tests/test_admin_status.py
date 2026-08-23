import pytest
from fastapi.testclient import TestClient

from tests.conftest import force_state, make_admin, override_get_db, register_and_login, seed_complaint

ADMIN_PATH = "/api/v1/admin/complaints"


def setup_resident(client: TestClient, email: str) -> None:
    register_and_login(client, name=email.split("@")[0].title(), email=email)


# ---------- PRIORITY ----------

def test_admin_can_change_priority(client: TestClient) -> None:
    headers = make_admin(client)
    setup_resident(client, "prio@example.com")
    cid = seed_complaint("prio@example.com")

    response = client.patch(f"{ADMIN_PATH}/{cid}/priority", json={"priority": "HIGH"}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["priority"] == "HIGH"
    assert body["updated_at"] >= body["created_at"]
    assert body["status"] == "OPEN"


def test_invalid_priority_rejected(client: TestClient) -> None:
    headers = make_admin(client)
    setup_resident(client, "badprio@example.com")
    cid = seed_complaint("badprio@example.com")

    response = client.patch(f"{ADMIN_PATH}/{cid}/priority", json={"priority": "URGENT"}, headers=headers)
    assert response.status_code == 422


def test_missing_complaint_returns_404(client: TestClient) -> None:
    headers = make_admin(client)
    assert client.get(f"{ADMIN_PATH}/99999", headers=headers).status_code == 404
    r = client.patch(
        f"{ADMIN_PATH}/99999/status", json={"status": "IN_PROGRESS"}, headers=headers
    )
    assert r.status_code == 404


# ---------- STATUS TRANSITIONS ----------

def test_open_to_in_progress_succeeds(client: TestClient) -> None:
    headers = make_admin(client)
    setup_resident(client, "t1@example.com")
    cid = seed_complaint("t1@example.com")

    response = client.patch(
        f"{ADMIN_PATH}/{cid}/status",
        json={"status": "IN_PROGRESS", "note": "Plumber assigned"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"
    assert response.json()["resolved_at"] is None


def test_in_progress_to_resolved_succeeds_and_sets_resolved_at(client: TestClient) -> None:
    headers = make_admin(client)
    setup_resident(client, "t2@example.com")
    cid = seed_complaint("t2@example.com")
    force_state(cid, status="IN_PROGRESS")

    response = client.patch(
        f"{ADMIN_PATH}/{cid}/status", json={"status": "RESOLVED"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "RESOLVED"
    assert response.json()["resolved_at"] is not None


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("OPEN", "RESOLVED"),
        ("IN_PROGRESS", "OPEN"),
        ("RESOLVED", "OPEN"),
        ("RESOLVED", "IN_PROGRESS"),
        ("OPEN", "OPEN"),
        ("IN_PROGRESS", "IN_PROGRESS"),
        ("RESOLVED", "RESOLVED"),
    ],
)
def test_invalid_transitions_rejected_with_409(
    client: TestClient, current: str, target: str
) -> None:
    headers = make_admin(client)
    email = f"tr.{current}.{target}@example.com".lower()
    setup_resident(client, email)
    cid = seed_complaint(email)
    if current != "OPEN":
        force_state(cid, status=current)

    response = client.patch(f"{ADMIN_PATH}/{cid}/status", json={"status": target}, headers=headers)
    assert response.status_code == 409


# ---------- HISTORY ----------

def test_history_records_actor_note_and_order(client: TestClient) -> None:
    headers = make_admin(client)
    setup_resident(client, "hist@example.com")
    cid = seed_complaint("hist@example.com")

    initial = client.get(f"{ADMIN_PATH}/{cid}/history", headers=headers).json()
    assert len(initial) == 1
    assert initial[0]["status"] == "OPEN"
    assert initial[0]["note"] == "Complaint created"

    client.patch(
        f"{ADMIN_PATH}/{cid}/status",
        json={"status": "IN_PROGRESS", "note": "Team assigned"},
        headers=headers,
    )

    me = client.get("/api/v1/auth/me", headers=headers).json()
    history = client.get(f"{ADMIN_PATH}/{cid}/history", headers=headers).json()

    assert [h["status"] for h in history] == ["OPEN", "IN_PROGRESS"]
    latest = history[-1]
    assert latest["actor_id"] == me["id"]
    assert latest["actor_name"] == "Admin User"
    assert latest["note"] == "Team assigned"


def test_failed_transition_creates_no_history_or_change(client: TestClient) -> None:
    headers = make_admin(client)
    setup_resident(client, "failh@example.com")
    cid = seed_complaint("failh@example.com")

    r = client.patch(f"{ADMIN_PATH}/{cid}/status", json={"status": "RESOLVED"}, headers=headers)
    assert r.status_code == 409

    history = client.get(f"{ADMIN_PATH}/{cid}/history", headers=headers).json()
    complaint = client.get(f"{ADMIN_PATH}/{cid}", headers=headers).json()
    assert len(history) == 1
    assert history[0]["status"] == "OPEN"
    assert complaint["status"] == "OPEN"


def test_atomicity_on_history_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    from sqlalchemy import func, select

    from app.models.complaint import Complaint, ComplaintStatusHistory
    from app.models.user import User
    from app.services import complaint_service

    db = next(override_get_db())
    try:
        user = db.scalar(select(User).where(User.email == "atomic-admin@example.com"))
        if user is None:
            from app.core.security import hash_password

            user = User(
                name="Atomic Admin",
                email="atomic-admin@example.com",
                password_hash=hash_password("password-123"),
                role="admin",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        complaint = complaint_service.create_complaint(
            db,
            resident=user,
            category="PLUMBING",
            description="atomic check",
        )
        cid = complaint.id
        admin_id = user.id
        before_count = db.scalar(select(func.count()).select_from(ComplaintStatusHistory))
    finally:
        db.close()

    def failing_add(db, history):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(
        "app.repositories.complaint_repository.add_status_history", failing_add
    )

    from app.services import admin_complaint_service as svc

    db = next(override_get_db())
    try:
        admin = db.get(User, admin_id)
        with pytest.raises(RuntimeError):
            svc.update_status(db, admin=admin, complaint_id=cid, new_status="IN_PROGRESS")
        db.rollback()

        after_count = db.scalar(select(func.count()).select_from(ComplaintStatusHistory))
        unchanged = db.get(Complaint, cid)
        assert after_count == before_count == 1
        assert unchanged.status == "OPEN"
    finally:
        db.close()


def test_non_resolved_complaints_have_null_resolved_at(client: TestClient) -> None:
    headers = make_admin(client)
    setup_resident(client, "nullres@example.com")
    open_cid = seed_complaint("nullres@example.com")
    wip_cid = seed_complaint("nullres@example.com")
    force_state(wip_cid, status="IN_PROGRESS")

    for cid in (open_cid, wip_cid):
        body = client.get(f"{ADMIN_PATH}/{cid}", headers=headers).json()
        assert body["resolved_at"] is None

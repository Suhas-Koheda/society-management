from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models.complaint import Complaint, ComplaintStatusHistory
from app.models.user import User
from tests.conftest import override_get_db, register_and_login


def create_complaint(client: TestClient, headers: dict, **overrides) -> dict:
    payload = {
        "category": "PLUMBING",
        "description": "Kitchen tap is leaking",
    }
    payload.update(overrides)
    return client.post("/api/v1/complaints", json=payload, headers=headers)


def test_create_complaint_success(client: TestClient) -> None:
    headers = register_and_login(client, name="Res A", email="a@example.com")
    response = create_complaint(client, headers)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"] > 0
    assert body["category"] == "PLUMBING"
    assert body["description"] == "Kitchen tap is leaking"
    assert body["status"] == "OPEN"
    assert body["priority"] == "LOW"
    assert body["resolved_at"] is None
    assert body["created_at"] and body["updated_at"]


def test_new_complaint_status_is_open(client: TestClient) -> None:
    headers = register_and_login(client, name="Res B", email="b@example.com")
    body = create_complaint(client, headers).json()
    assert body["status"] == "OPEN"


def test_new_complaint_priority_is_low(client: TestClient) -> None:
    headers = register_and_login(client, name="Res C", email="c@example.com")
    body = create_complaint(client, headers).json()
    assert body["priority"] == "LOW"


def test_resident_id_comes_from_jwt_not_body(client: TestClient) -> None:
    owner_headers = register_and_login(client, name="Owner", email="owner@example.com")
    other_headers = register_and_login(client, name="Other", email="other@example.com")

    db = next(override_get_db())
    try:
        other_id = db.scalar(select(User.id).where(User.email == "other@example.com"))
    finally:
        db.close()

    body = create_complaint(
        client,
        owner_headers,
        resident_id=other_id,
    ).json()
    assert body["resident_id"] != other_id

    owner_id = body["resident_id"]
    me = client.get("/api/v1/auth/me", headers=owner_headers).json()
    assert body["resident_id"] == me["id"]
    assert client.get(f"/api/v1/complaints/{body['id']}", headers=other_headers).status_code == 404


def test_initial_history_record_created_automatically(client: TestClient) -> None:
    headers = register_and_login(client, name="Hist User", email="hist@example.com")
    complaint_id = create_complaint(client, headers).json()["id"]

    response = client.get(f"/api/v1/complaints/{complaint_id}/history", headers=headers)
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    entry = history[0]
    assert entry["status"] == "OPEN"
    assert entry["note"] == "Complaint created"

    user_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    assert entry["actor_id"] == user_id


def test_resident_lists_only_own_complaints(client: TestClient) -> None:
    a_headers = register_and_login(client, name="List A", email="la@example.com")
    b_headers = register_and_login(client, name="List B", email="lb@example.com")

    create_complaint(client, a_headers)
    create_complaint(client, a_headers, category="ELECTRICAL", description="Fan broken")
    b_complaint = create_complaint(
        client, b_headers, category="SECURITY", description="Gate camera offline"
    ).json()

    response = client.get("/api/v1/complaints", headers=a_headers)
    assert response.status_code == 200
    listing = response.json()
    assert listing["total"] == 2
    returned_ids = {item["id"] for item in listing["items"]}
    assert b_complaint["id"] not in returned_ids
    assert all(item["description"] != "Gate camera offline" for item in listing["items"])

    b_listing = client.get("/api/v1/complaints", headers=b_headers).json()
    assert b_listing["total"] == 1
    assert b_listing["items"][0]["id"] == b_complaint["id"]


def test_cannot_view_other_residents_complaint(client: TestClient) -> None:
    a_headers = register_and_login(client, name="View A", email="va@example.com")
    b_headers = register_and_login(client, name="View B", email="vb@example.com")

    complaint_id = create_complaint(client, a_headers).json()["id"]

    assert client.get(f"/api/v1/complaints/{complaint_id}", headers=b_headers).status_code == 404
    assert client.get(f"/api/v1/complaints/{complaint_id}", headers=a_headers).status_code == 200


def test_cannot_view_other_residents_history(client: TestClient) -> None:
    a_headers = register_and_login(client, name="HistA", email="ha@example.com")
    b_headers = register_and_login(client, name="HistB", email="hb@example.com")

    complaint_id = create_complaint(client, a_headers).json()["id"]

    response = client.get(f"/api/v1/complaints/{complaint_id}/history", headers=b_headers)
    assert response.status_code == 404


def test_unauthenticated_requests_rejected(client: TestClient) -> None:
    assert client.post(
        "/api/v1/complaints",
        json={"category": "PLUMBING", "description": "x"},
    ).status_code == 401
    assert client.get("/api/v1/complaints").status_code == 401
    assert client.get("/api/v1/complaints/1").status_code == 401
    assert client.get("/api/v1/complaints/1/history").status_code == 401


@pytest.mark.parametrize("bad_description", ["", "   ", "\t\n"])
def test_empty_description_rejected(client: TestClient, bad_description: str) -> None:
    headers = register_and_login(client, name="Desc U", email="desc@example.com")
    response = create_complaint(client, headers, description=bad_description)
    assert response.status_code == 422


def test_invalid_category_rejected(client: TestClient) -> None:
    headers = register_and_login(client, name="Cat U", email="cat@example.com")
    response = create_complaint(client, headers, category="GARDENING")
    assert response.status_code == 422


def test_invalid_status_or_priority_rejected(client: TestClient) -> None:
    headers = register_and_login(client, name="SP U", email="sp@example.com")
    response = client.post(
        "/api/v1/complaints",
        json={
            "category": "PLUMBING",
            "description": "desc",
            "status": "RESOLVED",
            "priority": "HIGH",
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "OPEN"
    assert body["priority"] == "LOW"


def test_description_whitespace_trimmed_and_max_length_enforced(client: TestClient) -> None:
    headers = register_and_login(client, name="Trim U", email="trim@example.com")

    body = create_complaint(client, headers, description="  Leaking pipe under sink  ").json()
    assert body["description"] == "Leaking pipe under sink"

    too_long = "x" * 2001
    assert create_complaint(client, headers, description=too_long).status_code == 422


def test_complaint_and_history_are_atomic(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_add_status_history(db, history):
        raise RuntimeError("simulated history failure")

    monkeypatch.setattr(
        "app.repositories.complaint_repository.add_status_history",
        failing_add_status_history,
    )

    from app.services import complaint_service

    db = next(override_get_db())
    try:
        user = db.scalar(select(User).where(User.email == "atomic@example.com"))
        if user is None:
            from app.services import auth_service

            user = auth_service.register_user(
                db,
                name="Atomic U",
                email="atomic@example.com",
                password="password-123",
            )

        with pytest.raises(RuntimeError):
            complaint_service.create_complaint(
                db,
                resident=user,
                category="PLUMBING",
                description="should be rolled back",
            )
        db.rollback()

        complaints_count = db.scalar(select(func.count()).select_from(Complaint))
        history_count = db.scalar(select(func.count()).select_from(ComplaintStatusHistory))
        assert complaints_count == 0
        assert history_count == 0
    finally:
        db.close()


def test_history_ordered_oldest_to_newest(client: TestClient) -> None:
    headers = register_and_login(client, name="Order U", email="order@example.com")
    complaint_id = create_complaint(client, headers).json()["id"]

    db = next(override_get_db())
    try:
        user = db.scalar(select(User).where(User.email == "order@example.com"))
        initial = db.scalar(
            select(ComplaintStatusHistory).where(
                ComplaintStatusHistory.complaint_id == complaint_id
            )
        )
        t0 = initial.created_at
        db.add_all(
            [
                ComplaintStatusHistory(
                    complaint_id=complaint_id,
                    status="IN_PROGRESS",
                    actor_id=user.id,
                    note="in-progress entry",
                    created_at=t0 + timedelta(minutes=30),
                ),
                ComplaintStatusHistory(
                    complaint_id=complaint_id,
                    status="RESOLVED",
                    actor_id=user.id,
                    note="resolved entry",
                    created_at=t0 + timedelta(hours=2),
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    response = client.get(f"/api/v1/complaints/{complaint_id}/history", headers=headers)
    entries = response.json()
    notes = [entry["note"] for entry in entries]
    statuses = [entry["status"] for entry in entries]

    assert len(entries) == 3
    assert notes == ["Complaint created", "in-progress entry", "resolved entry"]
    assert statuses == ["OPEN", "IN_PROGRESS", "RESOLVED"]

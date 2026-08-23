from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.core.enums import ComplaintPriority, ComplaintStatus
from app.services.overdue_service import is_overdue
from tests.conftest import force_state, make_admin, override_get_db, register_and_login, seed_complaint

ADMIN_PATH = "/api/v1/admin/complaints"


def make_resident(client: TestClient, email: str) -> dict:
    return register_and_login(client, name=email.split("@")[0].title(), email=email)


class FakeComplaint:
    def __init__(self, status: str, created_at: datetime):
        self.status = status
        self.created_at = created_at


# ---------- PURE OVERDUE LOGIC ----------

def test_new_open_complaint_not_overdue() -> None:
    now = datetime(2026, 8, 1, 12, 0, 0)
    c = FakeComplaint("OPEN", now - timedelta(hours=1))
    assert is_overdue(c, 7, now) is False


def test_old_open_complaint_overdue() -> None:
    now = datetime(2026, 8, 1, 12, 0, 0)
    c = FakeComplaint("OPEN", now - timedelta(days=10))
    assert is_overdue(c, 7, now) is True


def test_old_in_progress_complaint_overdue() -> None:
    now = datetime(2026, 8, 1, 12, 0, 0)
    c = FakeComplaint("IN_PROGRESS", now - timedelta(days=10))
    assert is_overdue(c, 7, now) is True


def test_resolved_never_overdue() -> None:
    now = datetime(2026, 8, 1, 12, 0, 0)
    c = FakeComplaint("RESOLVED", now - timedelta(days=100))
    assert is_overdue(c, 7, now) is False


def test_boundary_exactly_at_threshold_not_overdue() -> None:
    created = datetime(2026, 7, 25, 12, 0, 0)
    threshold_deadline = created + timedelta(days=7)
    c = FakeComplaint("OPEN", created)

    assert is_overdue(c, 7, threshold_deadline) is False
    assert is_overdue(c, 7, threshold_deadline + timedelta(seconds=1)) is True


def test_changing_threshold_changes_result() -> None:
    now = datetime(2026, 8, 1, 12, 0, 0)
    c = FakeComplaint("OPEN", now - timedelta(days=3))
    assert is_overdue(c, 2, now) is True
    assert is_overdue(c, 5, now) is False


# ---------- FILTERING VIA API ----------

def _seed_mix(client: TestClient) -> None:
    make_resident(client, "od@example.com")
    overdue_open = seed_complaint("od@example.com", description="old-open")
    fresh_open = seed_complaint("od@example.com", description="fresh-open")
    old_wip = seed_complaint("od@example.com", description="old-wip")
    old_resolved = seed_complaint("od@example.com", description="old-resolved")
    force_state(overdue_open, age_days=30)
    force_state(fresh_open, age_days=1)
    force_state(old_wip, status="IN_PROGRESS", age_days=20)
    force_state(old_resolved, status="RESOLVED", age_days=30)


def test_filter_overdue_true(client: TestClient) -> None:
    headers = make_admin(client)
    _seed_mix(client)

    body = client.get(f"{ADMIN_PATH}?overdue=true&page_size=50", headers=headers).json()
    descriptions = {i["description"] for i in body["items"]}
    assert descriptions == {"old-open", "old-wip"}
    assert all(i["is_overdue"] for i in body["items"])


def test_filter_overdue_false(client: TestClient) -> None:
    headers = make_admin(client)
    _seed_mix(client)

    body = client.get(f"{ADMIN_PATH}?overdue=false&page_size=50", headers=headers).json()
    descriptions = {i["description"] for i in body["items"]}
    assert descriptions == {"fresh-open", "old-resolved"}


def test_overdue_with_status_and_priority_filters(client: TestClient) -> None:
    headers = make_admin(client)
    _seed_mix(client)

    body = client.get(
        f"{ADMIN_PATH}?overdue=true&status=IN_PROGRESS", headers=headers
    ).json()
    assert {i["description"] for i in body["items"]} == {"old-wip"}

    seed_complaint("od@example.com", description="high-overdue")
    high_id = None
    from sqlalchemy import select

    from app.models.complaint import Complaint

    db = next(override_get_db())
    try:
        row = db.scalar(select(Complaint).where(Complaint.description == "high-overdue"))
        row.created_at = row.created_at - timedelta(days=15)
        row.priority = "HIGH"
        db.commit()
    finally:
        db.close()

    body = client.get(
        f"{ADMIN_PATH}?overdue=true&priority=HIGH", headers=headers
    ).json()
    assert {i["description"] for i in body["items"]} == {"high-overdue"}


def test_overdue_ordered_first_then_priority(client: TestClient) -> None:
    headers = make_admin(client)
    _seed_mix(client)
    fresh_high = seed_complaint("od@example.com", description="fresh-high")
    force_state(fresh_high, priority="HIGH", age_days=1)

    descriptions = [
        i["description"]
        for i in client.get(f"{ADMIN_PATH}?page_size=50", headers=headers).json()["items"]
    ]
    overdue_set = {"old-open", "old-wip"}
    first_non_overdue = next(d for d in descriptions if d not in overdue_set)
    assert descriptions.index(first_non_overdue) > max(
        descriptions.index(d) for d in overdue_set
    )
    assert descriptions[descriptions.index(first_non_overdue):] == [
        "fresh-high",
        "fresh-open",
        "old-resolved",
    ]


def test_pagination_works_with_overdue_ordering(client: TestClient) -> None:
    headers = make_admin(client)
    _seed_mix(client)
    for i in range(5):
        cid = seed_complaint("od@example.com", description=f"bulk{i}")
        force_state(cid, age_days=15)

    page_one = client.get(f"{ADMIN_PATH}?page_size=4&page=1", headers=headers).json()
    page_two = client.get(f"{ADMIN_PATH}?page_size=4&page=2", headers=headers).json()

    assert page_one["total"] == len(page_one["items"]) + len(page_two["items"]) + 1
    ids_p1 = {i["id"] for i in page_one["items"]}
    ids_p2 = {i["id"] for i in page_two["items"]}
    assert not (ids_p1 & ids_p2)
    assert all(i["is_overdue"] for i in page_one["items"])


# ---------- SETTINGS ----------

SETTINGS_PATH = "/api/v1/admin/settings/overdue-threshold"


def test_get_threshold_default_when_missing(client: TestClient) -> None:
    headers = make_admin(client)
    response = client.get(SETTINGS_PATH, headers=headers)
    assert response.status_code == 200
    assert response.json()["threshold_days"] == 7


def test_admin_updates_threshold(client: TestClient) -> None:
    headers = make_admin(client)
    r = client.patch(SETTINGS_PATH, json={"threshold_days": 3}, headers=headers)
    assert r.status_code == 200
    assert r.json()["threshold_days"] == 3
    assert client.get(SETTINGS_PATH, headers=headers).json()["threshold_days"] == 3


def test_resident_cannot_read_or_update_settings(client: TestClient) -> None:
    make_admin(client)
    resident = make_resident(client, "setres@example.com")

    assert client.get(SETTINGS_PATH, headers=resident).status_code == 403
    assert (
        client.patch(SETTINGS_PATH, json={"threshold_days": 3}, headers=resident).status_code
        == 403
    )


def test_unauthenticated_cannot_access_settings(client: TestClient) -> None:
    assert client.get(SETTINGS_PATH).status_code == 401
    assert client.patch(SETTINGS_PATH, json={"threshold_days": 3}).status_code == 401


def test_invalid_thresholds_rejected(client: TestClient) -> None:
    headers = make_admin(client)
    for bad in [0, -1, 366]:
        assert (
            client.patch(SETTINGS_PATH, json={"threshold_days": bad}, headers=headers).status_code
            == 422
        ), bad
    assert (
        client.patch(SETTINGS_PATH, json={"threshold_days": "abc"}, headers=headers).status_code
        == 422
    )


def test_updated_threshold_changes_api_overdue_results(client: TestClient) -> None:
    headers = make_admin(client)
    _seed_mix(client)

    body = client.get(f"{ADMIN_PATH}?overdue=true&page_size=50", headers=headers).json()
    assert {i["description"] for i in body["items"]} == {"old-open", "old-wip"}

    client.patch(SETTINGS_PATH, json={"threshold_days": 45}, headers=headers)
    body = client.get(f"{ADMIN_PATH}?overdue=true&page_size=50", headers=headers).json()
    assert body["items"] == []

    client.patch(SETTINGS_PATH, json={"threshold_days": 1}, headers=headers)
    body = client.get(f"{ADMIN_PATH}?overdue=true&page_size=50", headers=headers).json()
    assert "fresh-open" in {i["description"] for i in body["items"]}


# ---------- DASHBOARD ----------

DASHBOARD_PATH = "/api/v1/admin/dashboard"


def test_dashboard_counts(client: TestClient) -> None:
    headers = make_admin(client)
    _seed_mix(client)

    response = client.get(DASHBOARD_PATH, headers=headers)
    assert response.status_code == 200
    body = response.json()

    assert body["total_complaints"] == 4
    assert body["by_status"]["OPEN"] == 2
    assert body["by_status"]["IN_PROGRESS"] == 1
    assert body["by_status"]["RESOLVED"] == 1
    assert body["by_category"]["PLUMBING"] == 4
    assert body["overdue_count"] == 2


def test_dashboard_excludes_resolved_from_overdue(client: TestClient) -> None:
    headers = make_admin(client)
    make_resident(client, "dashres@example.com")
    resolved = seed_complaint("dashres@example.com")
    force_state(resolved, status="RESOLVED", age_days=90)
    open_old = seed_complaint("dashres@example.com")
    force_state(open_old, age_days=90)

    body = client.get(DASHBOARD_PATH, headers=headers).json()
    assert body["overdue_count"] == 1


def test_resident_cannot_access_dashboard(client: TestClient) -> None:
    make_admin(client)
    resident = make_resident(client, "dres@example.com")
    assert client.get(DASHBOARD_PATH, headers=resident).status_code == 403


def test_unauthenticated_cannot_access_dashboard(client: TestClient) -> None:
    assert client.get(DASHBOARD_PATH).status_code == 401

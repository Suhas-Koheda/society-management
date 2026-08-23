from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models.user import User
from tests.conftest import make_admin, override_get_db, register_and_login, seed_complaint

ADMIN_PATH = "/api/v1/admin/complaints"


def make_resident(client: TestClient, email: str) -> dict:
    return register_and_login(client, name=email.split("@")[0].title(), email=email)


def test_admin_can_list_complaints(client: TestClient) -> None:
    headers = make_admin(client)
    response = client.get(ADMIN_PATH, headers=headers)
    assert response.status_code == 200
    body = response.json()
    for key in ("items", "page", "page_size", "total", "total_pages"):
        assert key in body


def test_resident_gets_403_on_all_admin_endpoints(client: TestClient) -> None:
    headers = make_resident(client, "r403@example.com")
    complaint_id = seed_complaint("r403@example.com")

    routes = [
        ("GET", ADMIN_PATH, None),
        ("GET", f"{ADMIN_PATH}/{complaint_id}", None),
        ("PATCH", f"{ADMIN_PATH}/{complaint_id}/priority", {"priority": "HIGH"}),
        ("PATCH", f"{ADMIN_PATH}/{complaint_id}/status", {"status": "IN_PROGRESS"}),
        ("GET", f"{ADMIN_PATH}/{complaint_id}/history", None),
    ]
    for method, path, payload in routes:
        call = getattr(client, method.lower())
        kwargs = {"headers": headers}
        if payload is not None:
            kwargs["json"] = payload
        assert call(path, **kwargs).status_code == 403, path


def test_unauthenticated_gets_401_on_admin_endpoints(client: TestClient) -> None:
    routes = [
        ("GET", ADMIN_PATH, None),
        ("GET", f"{ADMIN_PATH}/1", None),
        ("PATCH", f"{ADMIN_PATH}/1/priority", {"priority": "HIGH"}),
        ("PATCH", f"{ADMIN_PATH}/1/status", {"status": "IN_PROGRESS"}),
        ("GET", f"{ADMIN_PATH}/1/history", None),
    ]
    for method, path, payload in routes:
        call = getattr(client, method.lower())
        kwargs = {"json": payload} if payload is not None else {}
        assert call(path, **kwargs).status_code == 401, path


def test_admin_lists_all_residents_complaints(client: TestClient) -> None:
    headers = make_admin(client)
    make_resident(client, "l1@example.com")
    make_resident(client, "l2@example.com")
    id1 = seed_complaint("l1@example.com", description="one")
    id2 = seed_complaint("l2@example.com", description="two")

    body = client.get(ADMIN_PATH, headers=headers).json()
    returned = {item["id"] for item in body["items"]}
    assert {id1, id2} <= returned


def test_status_filter(client: TestClient) -> None:
    from tests.conftest import force_state

    headers = make_admin(client)
    make_resident(client, "sf@example.com")
    open_id = seed_complaint("sf@example.com")
    wip_id = seed_complaint("sf@example.com")
    force_state(wip_id, status="IN_PROGRESS")

    ids = [i["id"] for i in client.get(f"{ADMIN_PATH}?status=OPEN", headers=headers).json()["items"]]
    assert open_id in ids and wip_id not in ids


def test_category_filter(client: TestClient) -> None:
    headers = make_admin(client)
    make_resident(client, "cf@example.com")
    plumbing_id = seed_complaint("cf@example.com", category="PLUMBING")
    electrical_id = seed_complaint("cf@example.com", category="ELECTRICAL")

    ids = [
        i["id"]
        for i in client.get(f"{ADMIN_PATH}?category=ELECTRICAL", headers=headers).json()["items"]
    ]
    assert electrical_id in ids and plumbing_id not in ids


def test_priority_filter(client: TestClient) -> None:
    from tests.conftest import force_state

    headers = make_admin(client)
    make_resident(client, "pf@example.com")
    low_id = seed_complaint("pf@example.com")
    high_id = seed_complaint("pf@example.com")
    force_state(high_id, priority="HIGH")

    ids = [
        i["id"] for i in client.get(f"{ADMIN_PATH}?priority=HIGH", headers=headers).json()["items"]
    ]
    assert high_id in ids and low_id not in ids


def test_date_filter(client: TestClient) -> None:
    from datetime import timedelta

    from app.db.database import utcnow
    from tests.conftest import force_state

    headers = make_admin(client)
    make_resident(client, "df@example.com")
    old_id = seed_complaint("df@example.com")
    recent_id = seed_complaint("df@example.com")
    force_state(old_id, age_days=40)
    force_state(recent_id, age_days=2)

    date_from = (utcnow() - timedelta(days=10)).date().isoformat()
    date_to = utcnow().date().isoformat()
    ids = [
        i["id"]
        for i in client.get(
            f"{ADMIN_PATH}?date_from={date_from}&date_to={date_to}", headers=headers
        ).json()["items"]
    ]
    assert recent_id in ids and old_id not in ids


def test_multiple_filters_combined(client: TestClient) -> None:
    from tests.conftest import force_state

    headers = make_admin(client)
    make_resident(client, "mf@example.com")
    match_id = seed_complaint("mf@example.com", category="SECURITY")
    force_state(match_id, priority="HIGH")
    wrong_priority = seed_complaint("mf@example.com", category="SECURITY")
    wrong_category = seed_complaint("mf@example.com", category="CLEANING")
    force_state(wrong_category, priority="HIGH")

    ids = [
        i["id"]
        for i in client.get(
            f"{ADMIN_PATH}?category=SECURITY&priority=HIGH", headers=headers
        ).json()["items"]
    ]
    assert ids == [match_id]


def test_pagination(client: TestClient) -> None:
    headers = make_admin(client)
    make_resident(client, "pg@example.com")
    for i in range(25):
        seed_complaint("pg@example.com", description=f"c{i}")

    p1 = client.get(f"{ADMIN_PATH}?page=1&page_size=10", headers=headers).json()
    p3 = client.get(f"{ADMIN_PATH}?page=3&page_size=10", headers=headers).json()

    assert p1["total"] == 25 and p1["total_pages"] == 3
    assert len(p1["items"]) == 10 and len(p3["items"]) == 5
    assert p1["page"] == 1 and p3["page"] == 3
    seen = {i["id"] for i in p1["items"]} | {i["id"] for i in p3["items"]}
    assert len(seen) == 15


def test_ordering_deterministic(client: TestClient) -> None:
    from tests.conftest import force_state

    headers = make_admin(client)
    make_resident(client, "ord@example.com")
    low = seed_complaint("ord@example.com", description="low")
    medium = seed_complaint("ord@example.com", description="medium")
    high_old = seed_complaint("ord@example.com", description="high-old")
    high_new = seed_complaint("ord@example.com", description="high-new")
    force_state(low, priority="LOW", age_days=1)
    force_state(medium, priority="MEDIUM", age_days=1)
    force_state(high_old, priority="HIGH", age_days=2)
    force_state(high_new, priority="HIGH", age_days=1)

    descriptions = [
        i["description"]
        for i in client.get(f"{ADMIN_PATH}?page_size=10", headers=headers).json()["items"]
    ]
    assert descriptions == ["high-new", "high-old", "medium", "low"]


def test_admin_detail_includes_resident_without_sensitive_fields(client: TestClient) -> None:
    headers = make_admin(client)
    make_resident(client, "det@example.com")
    complaint_id = seed_complaint("det@example.com")

    body = client.get(f"{ADMIN_PATH}/{complaint_id}", headers=headers).json()
    assert body["resident"]["email"] == "det@example.com"
    assert "password_hash" not in str(body)

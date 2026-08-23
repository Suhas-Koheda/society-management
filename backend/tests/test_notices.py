from fastapi.testclient import TestClient

from tests.conftest import make_admin, override_get_db, register_and_login

NOTICES_PATH = "/api/v1/notices"
ADMIN_NOTICES_PATH = "/api/v1/admin/notices"


def make_resident(client: TestClient, email: str) -> dict:
    return register_and_login(client, name=email.split("@")[0].title(), email=email)


def create_notice(client: TestClient, headers: dict, **overrides) -> dict:
    payload = {"title": "Water cut", "content": "No water tomorrow.", "is_important": False}
    payload.update(overrides)
    return client.post(ADMIN_NOTICES_PATH, json=payload, headers=headers)


# ---------- AUTHORIZATION ----------

def test_resident_can_list_and_view(client: TestClient) -> None:
    admin = make_admin(client)
    created = create_notice(client, admin).json()
    resident = make_resident(client, "nres@example.com")

    assert client.get(NOTICES_PATH, headers=resident).status_code == 200
    r = client.get(f"{NOTICES_PATH}/{created['id']}", headers=resident)
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_resident_cannot_create_update_delete(client: TestClient) -> None:
    admin = make_admin(client)
    resident = make_resident(client, "nres2@example.com")
    created = create_notice(client, admin).json()

    assert (
        client.post(
            ADMIN_NOTICES_PATH,
            json={"title": "t", "content": "c"},
            headers=resident,
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"{ADMIN_NOTICES_PATH}/{created['id']}",
            json={"title": "x"},
            headers=resident,
        ).status_code
        == 403
    )
    assert (
        client.delete(f"{ADMIN_NOTICES_PATH}/{created['id']}", headers=resident).status_code == 403
    )


def test_unauthenticated_cannot_access_notices(client: TestClient) -> None:
    assert client.get(NOTICES_PATH).status_code == 401
    assert client.get(f"{NOTICES_PATH}/1").status_code == 401
    assert client.post(ADMIN_NOTICES_PATH, json={"title": "t", "content": "c"}).status_code == 401


# ---------- CREATION ----------

def test_admin_creates_notice_with_correct_created_by(client: TestClient) -> None:
    admin = make_admin(client)
    me = client.get("/api/v1/auth/me", headers=admin).json()

    body = create_notice(client, admin, is_important=True).json()
    assert body["created_by"] == me["id"]
    assert body["is_important"] is True


def test_client_cannot_spoof_created_by_or_timestamps(client: TestClient) -> None:
    admin = make_admin(client)
    body = create_notice(
        client,
        admin,
        created_by=9999,
        created_at="2000-01-01T00:00:00",
        updated_at="2000-01-01T00:00:00",
    )
    assert body.status_code == 201
    data = body.json()
    assert data["created_by"] != 9999
    assert not data["created_at"].startswith("2000")


def test_normal_notice_persisted(client: TestClient) -> None:
    admin = make_admin(client)
    body = create_notice(client, admin).json()
    assert body["is_important"] is False
    assert body["title"] == "Water cut"


def test_blank_title_content_rejected(client: TestClient) -> None:
    admin = make_admin(client)
    for bad in [{"title": "   ", "content": "c"}, {"title": "t", "content": ""}]:
        r = create_notice(client, admin, **bad)
        assert r.status_code == 422, bad


def test_whitespace_trimmed(client: TestClient) -> None:
    admin = make_admin(client)
    body = create_notice(
        client,
        admin,
        title="  Padded Title  ",
        content="   Padded content.  ",
    ).json()
    assert body["title"] == "Padded Title"
    assert body["content"] == "Padded content."


# ---------- UPDATES ----------

def test_admin_updates_fields_and_updated_at_changes(client: TestClient) -> None:
    admin = make_admin(client)
    created = create_notice(client, admin).json()

    r = client.patch(
        f"{ADMIN_NOTICES_PATH}/{created['id']}",
        json={"title": "New", "content": "New content", "is_important": True},
        headers=admin,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "New"
    assert body["is_important"] is True
    assert body["updated_at"] >= body["created_at"]


def test_created_by_immutable_on_update(client: TestClient) -> None:
    admin = make_admin(client)
    created = create_notice(client, admin).json()

    r = client.patch(
        f"{ADMIN_NOTICES_PATH}/{created['id']}",
        json={"created_by": 12345},
        headers=admin,
    )
    assert r.status_code == 200
    assert r.json()["created_by"] == created["created_by"]


def test_update_missing_notice_404(client: TestClient) -> None:
    admin = make_admin(client)
    r = client.patch(f"{ADMIN_NOTICES_PATH}/99999", json={"title": "x"}, headers=admin)
    assert r.status_code == 404


# ---------- LISTING / ORDERING / PAGINATION ----------

def test_important_first_then_newest_first(client: TestClient) -> None:
    admin = make_admin(client)

    normal_old = create_notice(client, admin, title="n1").json()
    important_new = create_notice(client, admin, title="i1", is_important=True).json()
    normal_new = create_notice(client, admin, title="n2").json()
    important_old = None
    from tests.conftest import override_get_db

    from app.models.notice import Notice

    db = next(override_get_db())
    try:
        notice = db.get(Notice, important_new["id"])
        notice.created_at = notice.created_at.replace(year=2000)
        db.commit()
        important_old = db.get(Notice, important_new["id"])
    finally:
        db.close()

    titles = [n["title"] for n in client.get(NOTICES_PATH, headers=admin).json()["items"]]
    assert titles == ["i1", "n2", "n1"]
    assert normal_old and important_old


def test_important_filter_true_false(client: TestClient) -> None:
    admin = make_admin(client)
    create_notice(client, admin, title="plain")
    create_notice(client, admin, title="pinned", is_important=True)

    only_imp = client.get(f"{NOTICES_PATH}?important=true", headers=admin).json()
    assert [n["title"] for n in only_imp["items"]] == ["pinned"]

    only_norm = client.get(f"{NOTICES_PATH}?important=false", headers=admin).json()
    assert [n["title"] for n in only_norm["items"]] == ["plain"]


def test_pagination_metadata(client: TestClient) -> None:
    admin = make_admin(client)
    for i in range(7):
        create_notice(client, admin, title=f"t{i}")

    page = client.get(f"{NOTICES_PATH}?page=2&page_size=3", headers=admin).json()
    assert page["total"] == 7
    assert page["total_pages"] == 3
    assert len(page["items"]) == 3
    assert page["page"] == 2


# ---------- DELETE ----------

def test_admin_deletes_notice(client: TestClient) -> None:
    admin = make_admin(client)
    created = create_notice(client, admin).json()

    r = client.delete(f"{ADMIN_NOTICES_PATH}/{created['id']}", headers=admin)
    assert r.status_code == 204

    listing = client.get(NOTICES_PATH, headers=admin).json()
    assert all(n["id"] != created["id"] for n in listing["items"])
    assert client.get(f"{NOTICES_PATH}/{created['id']}", headers=admin).status_code == 404


def test_delete_missing_notice_404(client: TestClient) -> None:
    admin = make_admin(client)
    assert client.delete(f"{ADMIN_NOTICES_PATH}/99999", headers=admin).status_code == 404

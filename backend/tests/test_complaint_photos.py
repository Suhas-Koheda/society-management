import pytest
from fastapi.testclient import TestClient

from app.services import storage_service
from app.services.storage_service import StorageBackend, UploadedImage
from tests.conftest import make_admin, override_get_db, register_and_login, seed_complaint


class FakeStorage(StorageBackend):
    def __init__(self, fail_upload: bool = False):
        self.uploaded: list[str] = []
        self.deleted: list[str] = []
        self.fail_upload = fail_upload

    def upload_image(self, data: bytes, content_type: str) -> UploadedImage:
        if self.fail_upload:
            raise storage_service.StorageError("boom")
        key = f"fake/{len(self.uploaded)}.jpg"
        self.uploaded.append(key)
        return UploadedImage(url=f"http://fake/{key}", storage_key=key)

    def delete_image(self, storage_key: str) -> None:
        self.deleted.append(storage_key)


@pytest.fixture
def fake_storage(monkeypatch: pytest.MonkeyPatch) -> FakeStorage:
    store = FakeStorage()
    monkeypatch.setattr(storage_service, "get_storage", lambda: store)
    return store


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"rest-of-image"
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"jpeg-data"
GIF_BYTES = b"GIF89a" + b"not-allowed"
WEBP_BYTES = b"RIFF\x00\x00\x00\x00WEBPVP8 "


def setup_owner(client: TestClient) -> tuple[dict, int]:
    headers = register_and_login(client, name="Owner", email="photo-owner@example.com")
    return headers, seed_complaint("photo-owner@example.com")


def upload(client: TestClient, headers: dict, cid: int, data: bytes, name="img.png", ctype="image/png"):
    return client.post(
        f"/api/v1/complaints/{cid}/photos",
        files={"file": (name, data, ctype)},
        headers=headers,
    )


def test_upload_jpeg_png_webp(client: TestClient, fake_storage: FakeStorage) -> None:
    headers, cid = setup_owner(client)
    for data, ctype in [
        (JPEG_BYTES, "image/jpeg"),
        (PNG_BYTES, "image/png"),
        (WEBP_BYTES, "image/webp"),
    ]:
        r = upload(client, headers, cid, data, ctype=ctype)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["url"].startswith("http://fake/")
        assert "storage_key" not in body


def test_invalid_type_rejected(client: TestClient, fake_storage: FakeStorage) -> None:
    headers, cid = setup_owner(client)
    r = upload(client, headers, cid, GIF_BYTES, ctype="image/gif")
    assert r.status_code == 415
    assert fake_storage.uploaded == []


def test_declared_type_mismatch_rejected(client: TestClient, fake_storage: FakeStorage) -> None:
    headers, cid = setup_owner(client)
    r = upload(client, headers, cid, PNG_BYTES, name="x.png", ctype="image/jpeg")
    assert r.status_code == 415


def test_oversized_file_rejected(
    client: TestClient, fake_storage: FakeStorage, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(storage_service, "max_upload_bytes", lambda: 10)
    headers, cid = setup_owner(client)
    r = upload(client, headers, cid, PNG_BYTES)
    assert r.status_code == 413
    assert fake_storage.uploaded == []


def test_unauthenticated_cannot_upload(client: TestClient, fake_storage: FakeStorage) -> None:
    _, cid = setup_owner(client)
    r = client.post(
        f"/api/v1/complaints/{cid}/photos", files={"file": ("i.png", PNG_BYTES, "image/png")}
    )
    assert r.status_code == 401


def test_cannot_upload_to_other_residents_complaint(
    client: TestClient, fake_storage: FakeStorage
) -> None:
    _, cid = setup_owner(client)
    other = register_and_login(client, name="Other", email="other-photo@example.com")
    r = upload(client, other, cid, PNG_BYTES)
    assert r.status_code == 404
    assert fake_storage.uploaded == []


def test_multiple_photos_allowed(client: TestClient, fake_storage: FakeStorage) -> None:
    headers, cid = setup_owner(client)
    for _ in range(3):
        assert upload(client, headers, cid, PNG_BYTES).status_code == 201
    listing = client.get(f"/api/v1/complaints/{cid}/photos", headers=headers).json()
    assert len(listing) == 3
    assert len({p["id"] for p in listing}) == 3


def test_resident_lists_own_photos(client: TestClient, fake_storage: FakeStorage) -> None:
    headers, cid = setup_owner(client)
    upload(client, headers, cid, PNG_BYTES)

    r = client.get(f"/api/v1/complaints/{cid}/photos", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_other_resident_cannot_list_photos(
    client: TestClient, fake_storage: FakeStorage
) -> None:
    _, cid = setup_owner(client)
    other = register_and_login(client, name="Other2", email="other2@example.com")
    assert client.get(f"/api/v1/complaints/{cid}/photos", headers=other).status_code == 404


def test_admin_can_list_any_complaint_photos(
    client: TestClient, fake_storage: FakeStorage
) -> None:
    headers, cid = setup_owner(client)
    upload(client, headers, cid, PNG_BYTES)

    admin = make_admin(client)
    r = client.get(f"/api/v1/admin/complaints/{cid}/photos", headers=admin)
    assert r.status_code == 200
    photos = r.json()
    assert len(photos) == 1
    assert "storage_key" not in photos[0]


def test_resident_cannot_use_admin_photo_endpoint(
    client: TestClient, fake_storage: FakeStorage
) -> None:
    _, cid = setup_owner(client)
    other = register_and_login(client, name="Other3", email="other3@example.com")
    r = client.get(f"/api/v1/admin/complaints/{cid}/photos", headers=other)
    assert r.status_code == 403


def test_storage_failure_creates_no_record(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = FakeStorage(fail_upload=True)
    monkeypatch.setattr(storage_service, "get_storage", lambda: store)

    from sqlalchemy import select

    from app.models.complaint import ComplaintPhoto

    headers, cid = setup_owner(client)
    r = upload(client, headers, cid, PNG_BYTES)
    assert r.status_code == 502

    db = next(override_get_db())
    try:
        count = len(db.scalars(select(ComplaintPhoto)).all())
        assert count == 0
    finally:
        db.close()


def test_db_failure_triggers_cleanup(
    client: TestClient, fake_storage: FakeStorage, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_add(db, photo):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.repositories.complaint_repository.add_photo", failing_add)

    headers, cid = setup_owner(client)
    with pytest.raises(RuntimeError):
        upload(client, headers, cid, PNG_BYTES)

    assert len(fake_storage.uploaded) == 1
    assert fake_storage.deleted == fake_storage.uploaded

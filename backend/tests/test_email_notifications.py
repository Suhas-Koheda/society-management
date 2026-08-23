import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.services import email_service, notice_service, storage_service  # noqa: F401
from app.services.email_service import EmailProvider
from tests.conftest import (
    force_state,
    make_admin,
    override_get_db,
    register_and_login,
    seed_complaint,
)

ADMIN_PATH = "/api/v1/admin/complaints"
ADMIN_NOTICES_PATH = "/api/v1/admin/notices"


class FakeEmailProvider(EmailProvider):
    def __init__(self, fail: bool = False):
        self.sent: list[tuple[str, str]] = []
        self.fail = fail

    def send_email(self, to_email: str, subject: str, html_body: str) -> None:
        if self.fail:
            raise email_service.EmailDeliveryError("smtp down")
        self.sent.append((to_email, subject))


@pytest.fixture
def fake_mail(monkeypatch: pytest.MonkeyPatch) -> FakeEmailProvider:
    provider = FakeEmailProvider()
    monkeypatch.setattr(email_service, "get_provider", lambda: provider)
    return provider


def setup_resident(client: TestClient) -> tuple[dict, int]:
    headers = register_and_login(client, name="Mail Res", email="mail-res@example.com")
    return headers, seed_complaint("mail-res@example.com")


def test_status_change_triggers_email(client: TestClient, fake_mail: FakeEmailProvider) -> None:
    headers, cid = setup_resident(client)
    admin = make_admin(client)

    r = client.patch(
        f"{ADMIN_PATH}/{cid}/status",
        json={"status": "IN_PROGRESS", "note": "Team assigned"},
        headers=admin,
    )
    assert r.status_code == 200

    assert len(fake_mail.sent) == 1
    to_email, subject = fake_mail.sent[0]
    assert to_email == "mail-res@example.com"
    assert f"#{cid}" in subject

    from sqlalchemy import select

    from app.models.complaint import Complaint

    db = next(override_get_db())
    try:
        complaint = db.get(Complaint, cid)
        body_check = complaint
    finally:
        db.close()


def test_resolved_transition_triggers_email(
    client: TestClient, fake_mail: FakeEmailProvider
) -> None:
    headers, cid = setup_resident(client)
    admin = make_admin(client)
    force_state(cid, status="IN_PROGRESS")

    client.patch(f"{ADMIN_PATH}/{cid}/status", json={"status": "RESOLVED"}, headers=admin)
    assert len(fake_mail.sent) == 1


def test_failed_transition_sends_no_email(
    client: TestClient, fake_mail: FakeEmailProvider
) -> None:
    headers, cid = setup_resident(client)
    admin = make_admin(client)

    r = client.patch(f"{ADMIN_PATH}/{cid}/status", json={"status": "RESOLVED"}, headers=admin)
    assert r.status_code == 409
    assert fake_mail.sent == []


def test_email_body_contains_expected_fields(
    client: TestClient, fake_mail: FakeEmailProvider, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[str] = []

    class RecordingProvider(FakeEmailProvider):
        def send_email(self, to_email: str, subject: str, html_body: str) -> None:
            captured.append(html_body)
            self.sent.append((to_email, subject))

    monkeypatch.setattr(email_service, "get_provider", lambda: RecordingProvider())

    _, cid = setup_resident(client)
    admin = make_admin(client)
    client.patch(
        f"{ADMIN_PATH}/{cid}/status",
        json={"status": "IN_PROGRESS", "note": "Plumber coming"},
        headers=admin,
    )

    html = captured[-1]
    assert "Mail Res" in html
    assert str(cid) in html
    assert "PLUMBING" in html
    assert "IN_PROGRESS" in html
    assert "Plumber coming" in html


def test_normal_notice_no_email(client: TestClient, fake_mail: FakeEmailProvider) -> None:
    admin = make_admin(client)
    r = client.post(
        ADMIN_NOTICES_PATH,
        json={"title": "Routine", "content": "Nothing special", "is_important": False},
        headers=admin,
    )
    assert r.status_code == 201
    assert fake_mail.sent == []


def test_important_notice_emails_residents(
    client: TestClient, fake_mail: FakeEmailProvider
) -> None:
    register_and_login(client, name="Res One", email="res1@example.com")
    register_and_login(client, name="Res Two", email="res2@example.com")
    admin = make_admin(client)

    r = client.post(
        ADMIN_NOTICES_PATH,
        json={"title": "Water outage", "content": "No water 10-14h", "is_important": True},
        headers=admin,
    )
    assert r.status_code == 201

    recipients = {to for to, _ in fake_mail.sent}
    assert {"res1@example.com", "res2@example.com"} <= recipients
    assert any("Water outage" in subj for _, subj in fake_mail.sent)


def test_promoting_notice_to_important_triggers_email(
    client: TestClient, fake_mail: FakeEmailProvider
) -> None:
    register_and_login(client, name="Res Three", email="res3@example.com")
    admin = make_admin(client)
    created = client.post(
        ADMIN_NOTICES_PATH,
        json={"title": "Later important", "content": "content"},
        headers=admin,
    ).json()
    assert fake_mail.sent == []

    client.patch(
        f"{ADMIN_NOTICES_PATH}/{created['id']}", json={"is_important": True}, headers=admin
    )
    assert any(to == "res3@example.com" for to, _ in fake_mail.sent)


def test_email_failure_does_not_corrupt_state(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    failing = FakeEmailProvider(fail=True)
    monkeypatch.setattr(email_service, "get_provider", lambda: failing)

    headers, cid = setup_resident(client)
    admin = make_admin(client)

    r = client.patch(
        f"{ADMIN_PATH}/{cid}/status",
        json={"status": "IN_PROGRESS"},
        headers=admin,
    )
    assert r.status_code == 200

    db = next(override_get_db())
    try:
        from sqlalchemy import select, func

        from app.models.complaint import Complaint, ComplaintStatusHistory

        complaint = db.get(Complaint, cid)
        history_count = db.scalar(select(func.count()).select_from(ComplaintStatusHistory))
        assert complaint.status == "IN_PROGRESS"
        assert history_count == 2
    finally:
        db.close()

import logging
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.notice import Notice
from app.repositories.notice_repository import get_all_recipient_emails

logger = logging.getLogger(__name__)

_RESEND_ENDPOINT = "https://api.resend.com/emails"


class EmailDeliveryError(Exception):
    pass


def _fmt(ts: datetime | None) -> str:
    return ts.isoformat(sep=" ") if ts else "n/a"


class EmailProvider:
    def send_email(self, to_email: str, subject: str, html_body: str) -> None:
        raise NotImplementedError


class ConsoleEmailProvider(EmailProvider):
    def send_email(self, to_email: str, subject: str, html_body: str) -> None:
        logger.info("[email:console] to=%s subject=%r", to_email, subject)


class ResendEmailProvider(EmailProvider):
    def __init__(self, api_key: str, from_email: str):
        self._api_key = api_key
        self._from = from_email

    def send_email(self, to_email: str, subject: str, html_body: str) -> None:
        try:
            response = httpx.post(
                _RESEND_ENDPOINT,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "from": self._from,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                },
                timeout=10.0,
            )
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Resend delivery failed for %s: %s", to_email, exc)
            raise EmailDeliveryError(str(exc)) from exc


def get_provider() -> EmailProvider:
    settings = get_settings()
    if settings.EMAIL_PROVIDER == "resend" and settings.RESEND_API_KEY:
        return ResendEmailProvider(settings.RESEND_API_KEY, settings.EMAIL_FROM)
    return ConsoleEmailProvider()


def _deliver(provider: EmailProvider, to_email: str, subject: str, html_body: str) -> bool:
    try:
        provider.send_email(to_email, subject, html_body)
        return True
    except Exception:
        return False


def _status_email_body(resident_name: str, complaint, note: str | None) -> tuple[str, str]:
    subject = f"[Society Tracker] Complaint #{complaint.id} status updated"
    note_html = (
        f"<p><b>Admin note:</b> {note}</p>" if note else ""
    )
    html = (
        f"<p>Hi {resident_name},</p>"
        f"<p>The status of your complaint has been updated.</p>"
        f"<ul>"
        f"<li>Complaint ID: {complaint.id}</li>"
        f"<li>Category: {complaint.category}</li>"
        f"<li>New status: <b>{complaint.status}</b></li>"
        f"{note_html}"
        f"<li>Updated at: {_fmt(complaint.updated_at)}</li>"
        f"</ul>"
    )
    return subject, html


def send_complaint_status_email(db: Session, complaint, admin_note: str | None = None) -> None:
    try:
        resident = complaint.resident
        if resident is None or not resident.email:
            return
        subject, html = _status_email_body(resident.name, complaint, admin_note)
        delivered = _deliver(get_provider(), resident.email, subject, html)
        if not delivered:
            logger.warning("Status-change email for complaint #%s was not delivered", complaint.id)
    except Exception as exc:
        logger.warning("Status-change email failed (ignored): %s", exc)


def send_important_notice_email(db: Session, notice: Notice) -> None:
    try:
        recipients = list(get_all_recipient_emails(db))
        if not recipients:
            return
        provider = get_provider()
        subject = f"[Society Tracker] Important notice: {notice.title}"
        html = (
            "<p>An important society notice has been published.</p>"
            f"<h3>{notice.title}</h3>"
            f"<div>{notice.content}</div>"
            f"<p style='color:#666'>Published at: {_fmt(notice.created_at)}</p>"
        )
        failures = 0
        for email in recipients:
            if not _deliver(provider, email, subject, html):
                failures += 1
        if failures:
            logger.warning("Important-notice email failed for %d recipient(s)", failures)
    except Exception as exc:
        logger.warning("Important-notice email failed (ignored): %s", exc)

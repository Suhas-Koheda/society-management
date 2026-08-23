import math
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.core.enums import ComplaintCategory, ComplaintPriority, ComplaintStatus
from app.db.database import utcnow
from app.models.complaint import Complaint
from app.models.user import User
from app.repositories import complaint_repository as repo
from app.repositories.complaint_repository import ComplaintFilters

ALLOWED_STATUS_TRANSITIONS: dict[ComplaintStatus, set[ComplaintStatus]] = {
    ComplaintStatus.OPEN: {ComplaintStatus.IN_PROGRESS},
    ComplaintStatus.IN_PROGRESS: {ComplaintStatus.RESOLVED},
    ComplaintStatus.RESOLVED: set(),
}

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class ComplaintNotFoundError(Exception):
    pass


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: ComplaintStatus, requested: ComplaintStatus):
        self.current = current
        self.requested = requested
        super().__init__(f"Transition {current} -> {requested} is not allowed")


def _resolve_date_range(
    date_from: date | None,
    date_to: date | None,
) -> tuple[datetime | None, datetime | None]:
    created_after = (
        datetime.combine(date_from, time.min) if date_from is not None else None
    )
    created_before = (
        datetime.combine(date_to + timedelta(days=1), time.min)
        if date_to is not None
        else None
    )
    return created_after, created_before


def list_complaints(
    db: Session,
    *,
    status: ComplaintStatus | None = None,
    category: ComplaintCategory | None = None,
    priority: ComplaintPriority | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    overdue: bool | None = None,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[Complaint], int, int]:
    from app.services import settings_service
    from app.services.overdue_service import overdue_cutoff

    page = max(page, DEFAULT_PAGE)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    threshold_days = settings_service.get_overdue_threshold_days(db)
    cutoff = overdue_cutoff(threshold_days)

    created_after, created_before = _resolve_date_range(date_from, date_to)
    filters = ComplaintFilters(
        status=str(status) if status else None,
        category=str(category) if category else None,
        priority=str(priority) if priority else None,
        created_after=created_after,
        created_before=created_before,
        overdue=overdue,
        overdue_cutoff=cutoff,
    )

    total = repo.count_complaints(db, filters)
    offset = (page - 1) * page_size
    complaints = repo.list_complaints_admin(db, filters, offset=offset, limit=page_size)
    return complaints, total, threshold_days


def get_complaint(db: Session, *, complaint_id: int) -> Complaint:
    complaint = repo.get_complaint_by_id(db, complaint_id)
    if complaint is None:
        raise ComplaintNotFoundError(complaint_id)
    return complaint


def update_priority(
    db: Session,
    *,
    admin: User,
    complaint_id: int,
    priority: ComplaintPriority,
) -> Complaint:
    complaint = get_complaint(db, complaint_id=complaint_id)
    repo.set_complaint_priority(db, complaint, str(priority))
    db.commit()
    db.refresh(complaint)
    return complaint


def update_status(
    db: Session,
    *,
    admin: User,
    complaint_id: int,
    new_status: ComplaintStatus,
    note: str | None = None,
) -> Complaint:
    complaint = get_complaint(db, complaint_id=complaint_id)

    current_status = ComplaintStatus(complaint.status)
    if new_status not in ALLOWED_STATUS_TRANSITIONS[current_status]:
        raise InvalidStatusTransitionError(current_status, new_status)

    resolved_at = utcnow() if new_status is ComplaintStatus.RESOLVED else None
    repo.set_complaint_status(db, complaint, str(new_status), resolved_at)

    from app.models.complaint import ComplaintStatusHistory

    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        status=str(new_status),
        actor_id=admin.id,
        note=note,
    )
    repo.add_status_history(db, history)

    db.commit()
    db.refresh(complaint)

    try:
        from app.services.email_service import send_complaint_status_email

        send_complaint_status_email(db, complaint, admin_note=note)
    except Exception:
        pass
    return complaint


def total_pages(total: int, page_size: int) -> int:
    return math.ceil(total / page_size) if total else 0


def get_history(
    db: Session,
    *,
    complaint_id: int,
) -> list[tuple[object, str, str]]:
    get_complaint(db, complaint_id=complaint_id)
    return repo.get_history_with_actors(db, complaint_id)

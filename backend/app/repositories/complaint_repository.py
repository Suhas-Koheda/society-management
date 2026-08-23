from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.complaint import Complaint, ComplaintStatusHistory
from app.models.user import User


@dataclass(frozen=True)
class ComplaintFilters:
    status: str | None = None
    category: str | None = None
    priority: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    overdue: bool | None = None
    overdue_cutoff: datetime | None = None


def _overdue_condition(cutoff: datetime):
    from sqlalchemy import and_

    return and_(
        Complaint.status != "RESOLVED",
        Complaint.created_at < cutoff,
    )


def _apply_filters(stmt, filters: ComplaintFilters):
    if filters.status is not None:
        stmt = stmt.where(Complaint.status == filters.status)
    if filters.category is not None:
        stmt = stmt.where(Complaint.category == filters.category)
    if filters.priority is not None:
        stmt = stmt.where(Complaint.priority == filters.priority)
    if filters.created_after is not None:
        stmt = stmt.where(Complaint.created_at >= filters.created_after)
    if filters.created_before is not None:
        stmt = stmt.where(Complaint.created_at < filters.created_before)
    if filters.overdue is not None and filters.overdue_cutoff is not None:
        condition = _overdue_condition(filters.overdue_cutoff)
        stmt = stmt.where(condition if filters.overdue else ~condition)
    return stmt


def add_complaint(db: Session, complaint: Complaint) -> Complaint:
    db.add(complaint)
    db.flush()
    return complaint


def get_complaint_by_id(db: Session, complaint_id: int) -> Complaint | None:
    return db.get(Complaint, complaint_id)


def get_complaints_for_resident(
    db: Session,
    resident_id: int,
) -> list[Complaint]:
    stmt = (
        select(Complaint)
        .where(Complaint.resident_id == resident_id)
        .order_by(Complaint.created_at.desc(), Complaint.id.desc())
    )
    return list(db.scalars(stmt))


def get_history_for_complaint(
    db: Session,
    complaint_id: int,
) -> list[ComplaintStatusHistory]:
    stmt = (
        select(ComplaintStatusHistory)
        .where(ComplaintStatusHistory.complaint_id == complaint_id)
        .order_by(
            ComplaintStatusHistory.created_at.asc(),
            ComplaintStatusHistory.id.asc(),
        )
    )
    return list(db.scalars(stmt))


def add_status_history(
    db: Session,
    history: ComplaintStatusHistory,
) -> ComplaintStatusHistory:
    db.add(history)
    db.flush()
    return history


def count_complaints(db: Session, filters: ComplaintFilters) -> int:
    stmt = select(func.count()).select_from(Complaint)
    stmt = _apply_filters(stmt, filters)
    return db.scalar(stmt) or 0


def list_complaints_admin(
    db: Session,
    filters: ComplaintFilters,
    offset: int,
    limit: int,
) -> list[Complaint]:
    from sqlalchemy import case

    priority_rank = case(
        (Complaint.priority == "HIGH", 0),
        (Complaint.priority == "MEDIUM", 1),
        else_=2,
    )
    order_by = []
    if filters.overdue_cutoff is not None:
        overdue_first = case((_overdue_condition(filters.overdue_cutoff), 0), else_=1)
        order_by.append(overdue_first.asc())
    order_by.extend(
        [
            priority_rank.asc(),
            Complaint.created_at.desc(),
            Complaint.id.desc(),
        ]
    )
    stmt = _apply_filters(select(Complaint), filters).order_by(*order_by)
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt))


def count_by_status(db: Session) -> dict[str, int]:
    rows = db.execute(select(Complaint.status, func.count()).group_by(Complaint.status))
    return {status: count for status, count in rows}


def count_by_category(db: Session) -> dict[str, int]:
    rows = db.execute(select(Complaint.category, func.count()).group_by(Complaint.category))
    return {category: count for category, count in rows}


def set_complaint_status(
    db: Session,
    complaint: Complaint,
    status: str,
    resolved_at: datetime | None,
) -> Complaint:
    complaint.status = status
    complaint.resolved_at = resolved_at
    db.flush()
    return complaint


def set_complaint_priority(
    db: Session,
    complaint: Complaint,
    priority: str,
) -> Complaint:
    complaint.priority = priority
    db.flush()
    return complaint


def get_history_with_actors(
    db: Session,
    complaint_id: int,
) -> list[tuple[ComplaintStatusHistory, str, str]]:
    stmt = (
        select(ComplaintStatusHistory, User.name, User.email)
        .join(User, ComplaintStatusHistory.actor_id == User.id)
        .where(ComplaintStatusHistory.complaint_id == complaint_id)
        .order_by(
            ComplaintStatusHistory.created_at.asc(),
            ComplaintStatusHistory.id.asc(),
        )
    )
    return [(row[0], row[1], row[2]) for row in db.execute(stmt)]


def add_photo(db, photo):
    db.add(photo)
    db.flush()
    return photo


def get_photos_for_complaint(db, complaint_id: int) -> list:
    from app.models.complaint import ComplaintPhoto

    stmt = (
        select(ComplaintPhoto)
        .where(ComplaintPhoto.complaint_id == complaint_id)
        .order_by(ComplaintPhoto.id.asc())
    )
    return list(db.scalars(stmt))

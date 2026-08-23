from sqlalchemy.orm import Session

from app.core.enums import ComplaintCategory, ComplaintPriority, ComplaintStatus
from app.models.complaint import Complaint, ComplaintStatusHistory
from app.models.user import User
from app.repositories import complaint_repository as repo

INITIAL_HISTORY_NOTE = "Complaint created"


def create_complaint(
    db: Session,
    *,
    resident: User,
    category: ComplaintCategory | str,
    description: str,
) -> Complaint:
    complaint = Complaint(
        resident_id=resident.id,
        category=category,
        description=description,
        status=ComplaintStatus.OPEN,
        priority=ComplaintPriority.LOW,
        resolved_at=None,
    )
    repo.add_complaint(db, complaint)

    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        status=ComplaintStatus.OPEN,
        actor_id=resident.id,
        note=INITIAL_HISTORY_NOTE,
    )
    repo.add_status_history(db, history)

    db.commit()
    db.refresh(complaint)
    return complaint


def get_resident_complaints(
    db: Session,
    *,
    resident_id: int,
) -> list[Complaint]:
    return repo.get_complaints_for_resident(db, resident_id)


def get_resident_complaint(
    db: Session,
    *,
    complaint_id: int,
    resident_id: int,
) -> Complaint | None:
    complaint = repo.get_complaint_by_id(db, complaint_id)
    if complaint is None or complaint.resident_id != resident_id:
        return None
    return complaint


def get_resident_complaint_history(
    db: Session,
    *,
    complaint_id: int,
    resident_id: int,
) -> list[ComplaintStatusHistory] | None:
    complaint = get_resident_complaint(
        db,
        complaint_id=complaint_id,
        resident_id=resident_id,
    )
    if complaint is None:
        return None
    return repo.get_history_for_complaint(db, complaint_id)

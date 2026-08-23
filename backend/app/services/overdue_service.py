from datetime import datetime, timedelta

from app.core.enums import ComplaintStatus
from app.db.database import utcnow

_OVERDUE_STATUSES = frozenset(
    {ComplaintStatus.OPEN, ComplaintStatus.IN_PROGRESS}
)


def is_overdue(
    complaint,
    threshold_days: int,
    now: datetime | None = None,
) -> bool:
    if complaint.status not in _OVERDUE_STATUSES:
        return False
    current = now if now is not None else utcnow()
    deadline = complaint.created_at + timedelta(days=threshold_days)
    return current > deadline


def overdue_cutoff(threshold_days: int, now: datetime | None = None) -> datetime:
    current = now if now is not None else utcnow()
    return current - timedelta(days=threshold_days)

from sqlalchemy.orm import Session

from app.repositories import complaint_repository as repo
from app.services import settings_service
from app.services.overdue_service import overdue_cutoff


def get_dashboard(db: Session) -> dict:
    threshold = settings_service.get_overdue_threshold_days(db)
    cutoff = overdue_cutoff(threshold)

    by_status = repo.count_by_status(db)
    by_category = repo.count_by_category(db)
    total = sum(by_status.values())
    overdue_count = repo.count_complaints(
        db,
        repo.ComplaintFilters(overdue=True, overdue_cutoff=cutoff),
    )

    return {
        "total_complaints": total,
        "by_status": by_status,
        "by_category": by_category,
        "overdue_count": overdue_count,
    }

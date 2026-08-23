from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.system_setting import SystemSetting

OVERDUE_THRESHOLD_KEY = "overdue_threshold_days"
DEFAULT_OVERDUE_THRESHOLD_DAYS = 7
MIN_OVERDUE_THRESHOLD_DAYS = 1
MAX_OVERDUE_THRESHOLD_DAYS = 365


def get_overdue_threshold_days(db: Session) -> int:
    raw = db.scalar(
        select(SystemSetting.value).where(SystemSetting.key == OVERDUE_THRESHOLD_KEY)
    )
    if raw is None:
        return DEFAULT_OVERDUE_THRESHOLD_DAYS
    try:
        days = int(str(raw).strip())
    except (TypeError, ValueError):
        return DEFAULT_OVERDUE_THRESHOLD_DAYS
    if MIN_OVERDUE_THRESHOLD_DAYS <= days <= MAX_OVERDUE_THRESHOLD_DAYS:
        return days
    return DEFAULT_OVERDUE_THRESHOLD_DAYS


def set_overdue_threshold_days(db: Session, days: int) -> int:
    setting = db.scalar(
        select(SystemSetting).where(SystemSetting.key == OVERDUE_THRESHOLD_KEY)
    )
    if setting is None:
        setting = SystemSetting(key=OVERDUE_THRESHOLD_KEY, value=str(days))
        db.add(setting)
    else:
        setting.value = str(days)
    db.commit()
    return days

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notice import Notice


def add_notice(db: Session, notice: Notice) -> Notice:
    db.add(notice)
    db.flush()
    return notice


def get_notice_by_id(db: Session, notice_id: int) -> Notice | None:
    return db.get(Notice, notice_id)


def list_notices(
    db: Session,
    *,
    important: bool | None = None,
    offset: int = 0,
    limit: int = 20,
) -> list[Notice]:
    stmt = select(Notice)
    if important is not None:
        stmt = stmt.where(Notice.is_important == important)
    stmt = stmt.order_by(
        Notice.is_important.desc(),
        Notice.created_at.desc(),
        Notice.id.desc(),
    )
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt))


def count_notices(db: Session, *, important: bool | None = None) -> int:
    stmt = select(func.count()).select_from(Notice)
    if important is not None:
        stmt = stmt.where(Notice.is_important == important)
    return db.scalar(stmt) or 0


def update_notice(db: Session, notice: Notice, **fields) -> Notice:
    for field_name, value in fields.items():
        setattr(notice, field_name, value)
    db.flush()
    return notice


def delete_notice(db: Session, notice: Notice) -> None:
    db.delete(notice)
    db.flush()


def get_all_recipient_emails(db: Session) -> list[str]:
    from app.models.user import User

    return list(db.scalars(select(User.email)))

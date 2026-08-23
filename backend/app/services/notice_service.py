import logging
import math

from sqlalchemy.orm import Session

from app.models.notice import Notice
from app.models.user import User
from app.repositories import notice_repository as repo
from app.schemas.notice import NoticeCreate, NoticeUpdate

logger = logging.getLogger(__name__)

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class NoticeNotFoundError(Exception):
    pass


def create_notice(db: Session, *, admin: User, payload: NoticeCreate) -> Notice:
    notice = Notice(
        title=payload.title,
        content=payload.content,
        is_important=payload.is_important,
        created_by=admin.id,
    )
    repo.add_notice(db, notice)
    db.commit()
    db.refresh(notice)

    if notice.is_important:
        _notify_important_notice(db, notice)
    return notice


def _notify_important_notice(db: Session, notice: Notice) -> None:
    try:
        from app.services.email_service import send_important_notice_email

        send_important_notice_email(db, notice)
    except Exception as exc:
        logger.warning("Important-notice notification failed: %s", exc)


def update_notice(
    db: Session,
    *,
    notice_id: int,
    payload: NoticeUpdate,
) -> Notice:
    notice = get_notice(db, notice_id=notice_id)

    fields = payload.model_dump(exclude_unset=True, exclude_none=False)
    changed = {k: v for k, v in fields.items() if v is not None}
    if not changed:
        return notice

    was_important = notice.is_important
    repo.update_notice(db, notice, **changed)
    db.commit()
    db.refresh(notice)

    if notice.is_important and not was_important:
        _notify_important_notice(db, notice)
    return notice


def delete_notice(db: Session, *, notice_id: int) -> None:
    notice = get_notice(db, notice_id=notice_id)
    repo.delete_notice(db, notice)
    db.commit()


def get_notice(db: Session, *, notice_id: int) -> Notice:
    notice = repo.get_notice_by_id(db, notice_id)
    if notice is None:
        raise NoticeNotFoundError(notice_id)
    return notice


def list_notices(
    db: Session,
    *,
    important: bool | None = None,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[Notice], int]:
    page = max(page, DEFAULT_PAGE)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    total = repo.count_notices(db, important=important)
    offset = (page - 1) * page_size
    notices = repo.list_notices(db, important=important, offset=offset, limit=page_size)
    return notices, total


def total_pages(total: int, page_size: int) -> int:
    return math.ceil(total / page_size) if total else 0

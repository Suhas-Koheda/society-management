from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_authenticated_user
from app.db.database import get_db
from app.schemas.notice import NoticeListResponse, NoticeResponse
from app.services import notice_service

router = APIRouter(
    prefix="/notices",
    tags=["notices"],
    dependencies=[Depends(require_authenticated_user)],
)

_UNAUTHORIZED = {401: {"description": "Missing or invalid authentication token"}}
_NOT_FOUND = {404: {"description": "Notice not found"}}


@router.get(
    "",
    response_model=NoticeListResponse,
    summary="List notices",
    description=(
        "Paginated notice list, important notices first, newest first within "
        "each group. Filter with ?important=true or ?important=false."
    ),
    responses=_UNAUTHORIZED,
)
def list_notices(
    important: bool | None = Query(default=None),
    page: int = Query(default=notice_service.DEFAULT_PAGE, ge=1),
    page_size: int = Query(
        default=notice_service.DEFAULT_PAGE_SIZE, ge=1, le=notice_service.MAX_PAGE_SIZE
    ),
    db: Session = Depends(get_db),
) -> NoticeListResponse:
    notices, total = notice_service.list_notices(
        db, important=important, page=page, page_size=page_size
    )
    return NoticeListResponse(
        items=[NoticeResponse.model_validate(n) for n in notices],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=notice_service.total_pages(total, page_size),
    )


@router.get(
    "/{notice_id}",
    response_model=NoticeResponse,
    summary="Get a single notice",
    responses={**_UNAUTHORIZED, **_NOT_FOUND},
)
def get_notice(
    notice_id: int,
    db: Session = Depends(get_db),
) -> NoticeResponse:
    try:
        notice = notice_service.get_notice(db, notice_id=notice_id)
    except notice_service.NoticeNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")
    return NoticeResponse.model_validate(notice)

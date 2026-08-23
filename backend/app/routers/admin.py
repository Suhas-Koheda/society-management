from datetime import date

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.core.enums import ComplaintCategory, ComplaintPriority, ComplaintStatus
from app.db.database import get_db, utcnow
from app.models.user import User
from app.schemas.admin import (
    AdminComplaintDetail,
    AdminComplaintHistoryItem,
    AdminComplaintListResponse,
    AdminComplaintListItem,
    OverdueThresholdResponse,
    OverdueThresholdUpdate,
    PriorityUpdate,
    StatusUpdate,
)
from app.schemas.complaint import ComplaintPhotoResponse
from app.schemas.notice import NoticeCreate, NoticeResponse, NoticeUpdate
from app.schemas.dashboard import DashboardResponse
from app.services import admin_complaint_service as service
from app.services import (
    complaint_photo_service,
    dashboard_service,
    notice_service,
    overdue_service,
    settings_service,
)

router = APIRouter(
    prefix="/admin/complaints",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)

settings_router = APIRouter(
    prefix="/admin/settings",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)

dashboard_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)

_UNAUTHORIZED = {401: {"description": "Missing or invalid authentication token"}}
_FORBIDDEN = {403: {"description": "Admin privileges required"}}
_NOT_FOUND = {404: {"description": "Complaint not found"}}


@router.get(
    "",
    response_model=AdminComplaintListResponse,
    summary="List all complaints with filters",
    description=(
        "Admin-only paginated complaint list. Supports filtering by status, "
        "category, priority, creation date range and overdue state. Ordered "
        "overdue-first, then HIGH > MEDIUM > LOW priority, then newest first."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
)
def list_complaints(
    status_filter: ComplaintStatus | None = Query(default=None, alias="status"),
    category: ComplaintCategory | None = None,
    priority: ComplaintPriority | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    overdue: bool | None = Query(default=None),
    page: int = Query(default=service.DEFAULT_PAGE, ge=1),
    page_size: int = Query(default=service.DEFAULT_PAGE_SIZE, ge=1, le=service.MAX_PAGE_SIZE),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminComplaintListResponse:
    complaints, total, threshold_days = service.list_complaints(
        db,
        status=status_filter,
        category=category,
        priority=priority,
        date_from=date_from,
        date_to=date_to,
        overdue=overdue,
        page=page,
        page_size=page_size,
    )
    now = utcnow()
    items = []
    for complaint in complaints:
        item = AdminComplaintListItem.model_validate(complaint)
        item.is_overdue = overdue_service.is_overdue(complaint, threshold_days, now)
        items.append(item)
    return AdminComplaintListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=service.total_pages(total, page_size),
    )


@router.get(
    "/{complaint_id}",
    response_model=AdminComplaintDetail,
    summary="Get any complaint with resident details",
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
)
def get_complaint(
    complaint_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminComplaintDetail:
    try:
        complaint = service.get_complaint(db, complaint_id=complaint_id)
    except service.ComplaintNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return AdminComplaintDetail.model_validate(complaint)


@router.patch(
    "/{complaint_id}/priority",
    response_model=AdminComplaintListItem,
    summary="Update complaint priority",
    description="Admin-only. Priority changes are not recorded in status history.",
    responses={
        **_UNAUTHORIZED,
        **_FORBIDDEN,
        **_NOT_FOUND,
        422: {"description": "Invalid priority value"},
    },
)
def update_priority(
    complaint_id: int,
    payload: PriorityUpdate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminComplaintListItem:
    try:
        complaint = service.update_priority(
            db,
            admin=user,
            complaint_id=complaint_id,
            priority=payload.priority,
        )
    except service.ComplaintNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return AdminComplaintListItem.model_validate(complaint)


@router.patch(
    "/{complaint_id}/status",
    response_model=AdminComplaintListItem,
    summary="Update complaint status",
    description=(
        "Admin-only strict lifecycle: OPEN -> IN_PROGRESS -> RESOLVED. "
        "Any other transition returns 409 Conflict. Every successful transition "
        "appends a status-history record in the same transaction. Resolving "
        "sets resolved_at; resolved complaints cannot be reopened."
    ),
    responses={
        **_UNAUTHORIZED,
        **_FORBIDDEN,
        **_NOT_FOUND,
        409: {"description": "Invalid status transition"},
    },
)
def update_status(
    complaint_id: int,
    payload: StatusUpdate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminComplaintListItem:
    try:
        complaint = service.update_status(
            db,
            admin=user,
            complaint_id=complaint_id,
            new_status=payload.status,
            note=payload.note,
        )
    except service.ComplaintNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    except service.InvalidStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot change status from {exc.current} to {exc.requested}",
        )
    return AdminComplaintListItem.model_validate(complaint)


@router.get(
    "/{complaint_id}/history",
    response_model=list[AdminComplaintHistoryItem],
    summary="Get complete status history",
    description="Returns the full status history of any complaint, oldest to newest.",
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
)
def get_history(
    complaint_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AdminComplaintHistoryItem]:
    try:
        rows = service.get_history(db, complaint_id=complaint_id)
    except service.ComplaintNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return [
        AdminComplaintHistoryItem(
            id=history.id,
            status=history.status,
            actor_id=history.actor_id,
            actor_name=name,
            actor_email=email,
            note=history.note,
            created_at=history.created_at,
        )
        for history, name, email in rows
    ]


@settings_router.get(
    "/overdue-threshold",
    response_model=OverdueThresholdResponse,
    summary="Get overdue threshold",
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
)
def get_overdue_threshold(
    db: Session = Depends(get_db),
) -> OverdueThresholdResponse:
    return OverdueThresholdResponse(
        threshold_days=settings_service.get_overdue_threshold_days(db)
    )


@settings_router.patch(
    "/overdue-threshold",
    response_model=OverdueThresholdResponse,
    summary="Update overdue threshold",
    description="Admin-only. Positive integer between 1 and 365 days.",
    responses={**_UNAUTHORIZED, **_FORBIDDEN, 422: {"description": "Invalid threshold"}},
)
def update_overdue_threshold(
    payload: OverdueThresholdUpdate,
    db: Session = Depends(get_db),
) -> OverdueThresholdResponse:
    days = settings_service.set_overdue_threshold_days(db, payload.threshold_days)
    return OverdueThresholdResponse(threshold_days=days)


@dashboard_router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Admin dashboard statistics",
    description=(
        "Aggregated counts: total complaints, grouped by status, grouped by "
        "category and current overdue count (same definition as the list filter)."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
)
def dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    return DashboardResponse(**dashboard_service.get_dashboard(db))


@router.get(
    "/{complaint_id}/photos",
    response_model=list[ComplaintPhotoResponse],
    summary="List photos of any complaint",
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
)
def admin_list_photos(
    complaint_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        photos = complaint_photo_service.get_photos(db, complaint_id=complaint_id)
    except complaint_photo_service.ComplaintNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return [
        ComplaintPhotoResponse(id=p.id, url=p.url, created_at=p.created_at) for p in photos
    ]


admin_notices_router = APIRouter(
    prefix="/admin/notices",
    tags=["notices"],
    dependencies=[Depends(require_admin)],
)

admin_users_router = APIRouter(
    prefix="/admin/users",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@admin_users_router.get(
    "",
    summary="List all users",
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
)
def list_users(
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id).all()
    return [
        {"id": u.id, "name": u.name, "email": u.email, "role": u.role, "created_at": str(u.created_at)}
        for u in users
    ]


@admin_users_router.patch(
    "/{user_id}/role",
    summary="Update user role",
    description="Admin-only. Set a user's role to 'admin' or 'resident'.",
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
)
def update_user_role(
    user_id: int,
    payload: dict,
    db: Session = Depends(get_db),
):
    role = payload.get("role")
    if role not in ("admin", "resident"):
        raise HTTPException(status_code=422, detail="Role must be 'admin' or 'resident'")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


@admin_notices_router.post(
    "",
    response_model=NoticeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a notice",
    description=(
        "Admin-only. created_by is set to the authenticated admin. Important "
        "notices trigger resident email notifications after the commit."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, 422: {"description": "Validation error"}},
)
def create_notice(
    payload: NoticeCreate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> NoticeResponse:
    notice = notice_service.create_notice(db, admin=user, payload=payload)
    return NoticeResponse.model_validate(notice)


@admin_notices_router.patch(
    "/{notice_id}",
    response_model=NoticeResponse,
    summary="Update a notice",
    description="Admin-only. id, created_by and created_at cannot be changed.",
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
)
def update_notice(
    notice_id: int,
    payload: NoticeUpdate,
    db: Session = Depends(get_db),
) -> NoticeResponse:
    try:
        notice = notice_service.update_notice(db, notice_id=notice_id, payload=payload)
    except notice_service.NoticeNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")
    return NoticeResponse.model_validate(notice)


@admin_notices_router.delete(
    "/{notice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notice",
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
)
def delete_notice(
    notice_id: int,
    db: Session = Depends(get_db),
):
    try:
        notice_service.delete_notice(db, notice_id=notice_id)
    except notice_service.NoticeNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")

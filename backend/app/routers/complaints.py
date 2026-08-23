from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_authenticated_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintHistoryResponse,
    ComplaintListResponse,
    ComplaintPhotoResponse,
    ComplaintResponse,
)
from app.services import complaint_photo_service, complaint_service
from app.services.auth_service import EmailAlreadyRegisteredError  # noqa: F401
from app.services.complaint_photo_service import ComplaintNotFoundError as PhotoNotFound
from app.services.storage_service import (
    FileTooLargeError,
    StorageError,
    UnsupportedFileTypeError,
    storage_dependency,
)

router = APIRouter(prefix="/complaints", tags=["complaints"])

_UNAUTHORIZED = {401: {"description": "Missing or invalid authentication token"}}
_NOT_FOUND = {404: {"description": "Complaint not found"}}


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a complaint",
    description=(
        "Creates a complaint for the authenticated resident. "
        "Status is always initialized to OPEN, priority to LOW, and "
        "resolved_at stays NULL. An initial OPEN status-history record "
        "is created in the same transaction."
    ),
    responses=_UNAUTHORIZED,
)
def create_complaint(
    payload: ComplaintCreate,
    user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> ComplaintResponse:
    complaint = complaint_service.create_complaint(
        db,
        resident=user,
        category=payload.category,
        description=payload.description,
    )
    return ComplaintResponse.model_validate(complaint)


@router.get(
    "",
    response_model=ComplaintListResponse,
    summary="List my complaints",
    description="Returns only the complaints belonging to the authenticated resident, newest first.",
    responses=_UNAUTHORIZED,
)
def list_complaints(
    user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> ComplaintListResponse:
    complaints = complaint_service.get_resident_complaints(db, resident_id=user.id)
    return ComplaintListResponse(
        items=[ComplaintResponse.model_validate(c) for c in complaints],
        total=len(complaints),
    )


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Get one of my complaints",
    description=(
        "Returns the complaint only if it belongs to the authenticated resident; "
        "otherwise responds with 404 so ownership of unknown IDs is not revealed."
    ),
    responses={**_UNAUTHORIZED, **_NOT_FOUND},
)
def get_complaint(
    complaint_id: int,
    user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> ComplaintResponse:
    complaint = complaint_service.get_resident_complaint(
        db,
        complaint_id=complaint_id,
        resident_id=user.id,
    )
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return ComplaintResponse.model_validate(complaint)


@router.get(
    "/{complaint_id}/history",
    response_model=list[ComplaintHistoryResponse],
    summary="Get complaint status history",
    description=(
        "Returns the status history of one of the resident's own complaints, "
        "ordered oldest to newest. Returns 404 for complaints owned by others."
    ),
    responses={**_UNAUTHORIZED, **_NOT_FOUND},
)
def get_complaint_history(
    complaint_id: int,
    user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> list[ComplaintHistoryResponse]:
    history = complaint_service.get_resident_complaint_history(
        db,
        complaint_id=complaint_id,
        resident_id=user.id,
    )
    if history is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return [ComplaintHistoryResponse.model_validate(h) for h in history]


@router.post(
    "/{complaint_id}/photos",
    response_model=ComplaintPhotoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a photo for my complaint",
    description=(
        "Resident-only. Attaches an image (JPEG, PNG or WebP) to the "
        "authenticated resident's own complaint. Max size configurable via "
        "MAX_UPLOAD_SIZE_MB (default 5 MB). The binary is stored in external "
        "object storage; only metadata is persisted."
    ),
    responses={
        **_UNAUTHORIZED,
        **_NOT_FOUND,
        413: {"description": "File exceeds maximum allowed size"},
        415: {"description": "Unsupported or mismatched image type"},
        502: {"description": "Image storage unavailable"},
    },
)
def upload_photo(
    complaint_id: int,
    file: UploadFile,
    user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
    storage=Depends(storage_dependency),
) -> ComplaintPhotoResponse:
    try:
        photo = complaint_photo_service.upload_photo(
            db,
            file=file,
            storage=storage,
            complaint_id=complaint_id,
            resident=user,
        )
    except PhotoNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    except FileTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc))
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Image storage is unavailable"
        )
    return ComplaintPhotoResponse(id=photo.id, url=photo.url, created_at=photo.created_at)


@router.get(
    "/{complaint_id}/photos",
    response_model=list[ComplaintPhotoResponse],
    summary="List photos of my complaint",
    responses={**_UNAUTHORIZED, **_NOT_FOUND},
)
def list_photos(
    complaint_id: int,
    user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> list[ComplaintPhotoResponse]:
    try:
        photos = complaint_photo_service.get_photos(
            db, complaint_id=complaint_id, resident=user
        )
    except PhotoNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return [
        ComplaintPhotoResponse(id=p.id, url=p.url, created_at=p.created_at) for p in photos
    ]

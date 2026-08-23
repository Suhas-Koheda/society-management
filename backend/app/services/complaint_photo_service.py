import logging

from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.complaint import Complaint, ComplaintPhoto
from app.models.user import User
from app.services.storage_service import (
    StorageBackend,
    StorageError,
    validate_image,
)

logger = logging.getLogger(__name__)


class ComplaintNotFoundError(Exception):
    pass


def _get_owned_complaint(
    db: Session,
    *,
    complaint_id: int,
    resident_id: int | None = None,
) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise ComplaintNotFoundError(complaint_id)
    if resident_id is not None and complaint.resident_id != resident_id:
        raise ComplaintNotFoundError(complaint_id)
    return complaint


def upload_photo(
    db: Session,
    *,
    file: UploadFile,
    storage: StorageBackend,
    complaint_id: int,
    resident: User,
) -> ComplaintPhoto:
    complaint = _get_owned_complaint(db, complaint_id=complaint_id, resident_id=resident.id)

    data = file.file.read()
    content_type = validate_image(data, file.content_type)

    uploaded = storage.upload_image(data, content_type)

    from app.repositories.complaint_repository import add_photo

    photo = ComplaintPhoto(
        complaint_id=complaint.id,
        url=uploaded.url,
        storage_key=uploaded.storage_key,
    )
    try:
        add_photo(db, photo)
        db.commit()
        db.refresh(photo)
    except Exception:
        db.rollback()
        logger.warning("DB insert failed after upload; cleaning up %s", uploaded.storage_key)
        try:
            storage.delete_image(uploaded.storage_key)
        except StorageError:
            pass
        raise
    return photo


def get_photos(
    db: Session,
    *,
    complaint_id: int,
    resident: User | None = None,
) -> list[ComplaintPhoto]:
    if resident is not None:
        _get_owned_complaint(db, complaint_id=complaint_id, resident_id=resident.id)
    else:
        _get_owned_complaint(db, complaint_id=complaint_id)
    from app.repositories.complaint_repository import get_photos_for_complaint

    return get_photos_for_complaint(db, complaint_id)

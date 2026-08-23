import logging
from base64 import b64encode
from dataclasses import dataclass
from io import BytesIO
from uuid import uuid4

from fastapi import Depends

from app.core.config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
]


@dataclass(frozen=True)
class UploadedImage:
    url: str
    storage_key: str


class StorageError(Exception):
    pass


class UnsupportedFileTypeError(StorageError):
    pass


class FileTooLargeError(StorageError):
    pass


def max_upload_bytes() -> int:
    return get_settings().MAX_UPLOAD_SIZE_MB * 1024 * 1024


def sniff_image_type(data: bytes) -> str | None:
    for signature, content_type in _MAGIC_SIGNATURES:
        if data.startswith(signature):
            return content_type
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image(data: bytes, declared_content_type: str | None) -> str:
    if len(data) > max_upload_bytes():
        raise FileTooLargeError("File exceeds the maximum allowed size")

    sniffed = sniff_image_type(data)
    if sniffed is None:
        raise UnsupportedFileTypeError("Unsupported image type")
    if (
        declared_content_type
        and declared_content_type != "application/octet-stream"
        and declared_content_type != sniffed
    ):
        raise UnsupportedFileTypeError("Declared content type does not match file contents")
    return sniffed


class StorageBackend:
    def upload_image(self, data: bytes, content_type: str) -> UploadedImage:
        raise NotImplementedError

    def delete_image(self, storage_key: str) -> None:
        raise NotImplementedError


class CloudinaryStorage(StorageBackend):
    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        self._uploader = cloudinary.uploader

    def upload_image(self, data: bytes, content_type: str) -> UploadedImage:
        try:
            data_uri = f"data:{content_type};base64,{b64encode(data).decode('ascii')}"
            result = self._uploader.upload(
                data_uri,
                public_id=f"complaints/{uuid4().hex}",
                resource_type="image",
                invalidate=True,
            )
        except Exception as exc:
            logger.warning("Cloudinary upload failed: %s", exc)
            raise StorageError("Image storage is unavailable") from exc

        url = result.get("secure_url") or result.get("url")
        if not url:
            raise StorageError("Storage provider returned no URL")
        return UploadedImage(url=url, storage_key=result["public_id"])

    def delete_image(self, storage_key: str) -> None:
        try:
            self._uploader.destroy(storage_key, resource_type="image", invalidate=True)
        except Exception as exc:
            logger.warning("Cloudinary destroy failed for %s: %s", storage_key, exc)


class ConsoleStorage(StorageBackend):
    def upload_image(self, data: bytes, content_type: str) -> UploadedImage:
        key = f"console/{uuid4().hex}"
        logger.info("[ConsoleStorage] stored %s (%s bytes, %s)", key, len(data), content_type)
        return UploadedImage(url=f"memory://{key}", storage_key=key)

    def delete_image(self, storage_key: str) -> None:
        logger.info("[ConsoleStorage] deleted %s", storage_key)


def get_storage() -> StorageBackend:
    settings = get_settings()
    if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
        return CloudinaryStorage(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )
    return ConsoleStorage()


def storage_dependency() -> StorageBackend:
    return get_storage()


DependsStorage = Depends(storage_dependency)

_BYTES_IO = BytesIO

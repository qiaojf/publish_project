from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.constants import ALLOWED_EXTENSIONS, ContentType
from app.core.exceptions import InvalidFileError
from app.utils.paths import safe_child


def validate_upload_name(filename: str, content_type: ContentType) -> str:
    if not filename or filename in {".", ".."} or "/" in filename or "\\" in filename or Path(filename).is_absolute():
        raise InvalidFileError("文件名不安全")
    suffix = Path(filename).suffix.lower()
    allowed = ALLOWED_EXTENSIONS[content_type]
    if allowed and suffix not in allowed:
        expected = "、".join(sorted(allowed))
        raise InvalidFileError(f"{content_type.value} 类型仅支持：{expected}")
    return filename


async def save_upload(upload: UploadFile, content_id: int, content_type: ContentType) -> tuple[str, str, int]:
    settings = get_settings()
    original_name = validate_upload_name(upload.filename or "", content_type)
    suffix = Path(original_name).suffix.lower()
    directory = safe_child(settings.source_storage_root, str(content_id))
    directory.mkdir(parents=True, exist_ok=True)
    destination = safe_child(directory, f"{uuid4().hex}{suffix}")
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    size = 0
    try:
        with destination.open("wb") as target:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise InvalidFileError(f"文件不能超过 {settings.max_upload_size_mb} MB")
                target.write(chunk)
        if size == 0:
            raise InvalidFileError("上传文件不能为空")
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()
    return original_name, str(destination), size


def remove_source(path: str | None) -> None:
    if not path:
        return
    settings = get_settings()
    candidate = Path(path).resolve()
    if candidate.is_relative_to(settings.source_storage_root.resolve()):
        candidate.unlink(missing_ok=True)

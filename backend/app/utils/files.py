import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.constants import ALLOWED_EXTENSIONS, ContentType
from app.core.exceptions import InvalidFileError
from app.utils.paths import safe_child


@dataclass(frozen=True)
class StoredSource:
    path: str
    display_name: str | None
    files: list[dict[str, object]]
    is_directory: bool
    total_size: int


def validate_upload_name(filename: str, content_type: ContentType) -> str:
    if not filename or filename in {".", ".."} or "/" in filename or "\\" in filename or Path(filename).is_absolute():
        raise InvalidFileError("文件名不安全")
    suffix = Path(filename).suffix.lower()
    allowed = ALLOWED_EXTENSIONS[content_type]
    if allowed and suffix not in allowed:
        expected = "、".join(sorted(allowed))
        raise InvalidFileError(f"{content_type.value} 类型仅支持：{expected}")
    return filename


def validate_relative_upload_path(value: str, content_type: ContentType, *, enforce_extension: bool = True) -> str:
    normalized = value.replace("\\", "/").strip("/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or len(normalized) > 1000
        or path.is_absolute()
        or any(part in {"", ".", ".."} or "\x00" in part for part in path.parts)
    ):
        raise InvalidFileError("文件夹中包含不安全的文件路径")
    if enforce_extension:
        validate_upload_name(path.name, content_type)
    return path.as_posix()


async def save_uploads(
    uploads: list[UploadFile], relative_paths: list[str] | None, content_id: int, content_type: ContentType,
) -> StoredSource:
    if not uploads:
        raise InvalidFileError("请选择至少一个文件")
    if relative_paths and len(relative_paths) != len(uploads):
        raise InvalidFileError("文件与相对路径数量不一致")

    settings = get_settings()
    paths = relative_paths or [upload.filename or "" for upload in uploads]
    is_directory = len(uploads) > 1 or any("/" in path.replace("\\", "/").strip("/") for path in paths)
    normalized_paths = [
        validate_relative_upload_path(
            path or upload.filename or "", content_type, enforce_extension=not is_directory,
        )
        for upload, path in zip(uploads, paths)
    ]
    allowed = ALLOWED_EXTENSIONS[content_type]
    if is_directory and allowed and not any(Path(path).suffix.lower() in allowed for path in normalized_paths):
        expected = "、".join(sorted(allowed))
        raise InvalidFileError(f"上传文件夹必须至少包含一个主文件：{expected}")
    lowered = [path.casefold() for path in normalized_paths]
    if len(lowered) != len(set(lowered)):
        raise InvalidFileError("上传内容中存在重复文件路径")

    content_root = safe_child(settings.source_storage_root, str(content_id))
    content_root.mkdir(parents=True, exist_ok=True)
    bundle_root = safe_child(content_root, uuid4().hex)
    bundle_root.mkdir(parents=True, exist_ok=False)
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    total_size = 0
    metadata: list[dict[str, object]] = []
    try:
        for upload, relative_path in zip(uploads, normalized_paths):
            destination = safe_child(bundle_root, *PurePosixPath(relative_path).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            file_size = 0
            with destination.open("wb") as target:
                while chunk := await upload.read(1024 * 1024):
                    file_size += len(chunk)
                    total_size += len(chunk)
                    if total_size > max_bytes:
                        raise InvalidFileError(f"上传文件总大小不能超过 {settings.max_upload_size_mb} MB")
                    target.write(chunk)
            if file_size == 0:
                raise InvalidFileError(f"上传文件不能为空：{relative_path}")
            metadata.append({"name": PurePosixPath(relative_path).name, "relative_path": relative_path, "size": file_size})
    except Exception:
        shutil.rmtree(bundle_root, ignore_errors=True)
        raise
    finally:
        for upload in uploads:
            await upload.close()

    if is_directory:
        return StoredSource(str(bundle_root), None, metadata, True, total_size)
    only_path = safe_child(bundle_root, *PurePosixPath(normalized_paths[0]).parts)
    return StoredSource(str(only_path), metadata[0]["name"], metadata, False, total_size)


async def save_upload(upload: UploadFile, content_id: int, content_type: ContentType) -> tuple[str, str, int]:
    stored = await save_uploads([upload], None, content_id, content_type)
    return str(stored.display_name), stored.path, stored.total_size


def remove_source(path: str | None) -> None:
    if not path:
        return
    settings = get_settings()
    candidate = Path(path).resolve()
    source_root = settings.source_storage_root.resolve()
    if not candidate.is_relative_to(source_root):
        return
    if candidate.is_dir():
        shutil.rmtree(candidate, ignore_errors=True)
    else:
        candidate.unlink(missing_ok=True)
        parent = candidate.parent
        if parent != source_root and parent.is_relative_to(source_root):
            try:
                parent.rmdir()
            except OSError:
                pass

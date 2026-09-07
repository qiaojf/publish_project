from __future__ import annotations

from pathlib import Path
from pathlib import PurePosixPath
from urllib.parse import quote

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.constants import ContentType, PublishStatus, ReviewAction, ReviewStatus
from app.core.config import get_settings
from app.core.exceptions import BusinessRuleError, InvalidFileError, PermissionDenied, ResourceNotFound
from app.db.base import utc_now
from app.db.models.content import Content
from app.db.models.user import User
from app.repositories.content_repository import ContentRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.publish_target_repository import PublishTargetRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.common import PageResult
from app.schemas.content import ContentPayload, ContentPreview, ContentPreviewFile, ContentRead
from app.services.category_service import CategoryService
from app.services.publish_target_service import PublishTargetService
from app.services.serializers import content_to_read
from app.utils.files import remove_source, save_uploads, validate_relative_upload_path
from app.utils.document_preview import build_document_preview


class ContentService:
    @staticmethod
    def _content_body(value: str | None) -> str | None:
        return None if not value or value.strip().lower() == "null" else value

    @staticmethod
    def _preview_source(content: Content) -> Path | None:
        if not content.source_file_path:
            return None
        candidate = Path(content.source_file_path).resolve()
        root = get_settings().source_storage_root.resolve()
        return candidate if candidate.is_relative_to(root) and candidate.exists() else None

    @staticmethod
    def _source_metadata(content: Content) -> list[dict[str, object]]:
        if content.source_files:
            return list(content.source_files)
        if content.source_file_name:
            return [{"name": content.source_file_name, "relative_path": content.source_file_name, "size": None}]
        return []

    @classmethod
    def _source_entry(cls, content: Content, relative_path: str) -> Path | None:
        source = cls._preview_source(content)
        if not source:
            return None
        if source.is_file():
            expected = content.source_file_name or source.name
            return source if relative_path == expected else None
        normalized = validate_relative_upload_path(
            relative_path, ContentType(content.content_type), enforce_extension=False,
        )
        candidate = source.joinpath(*PurePosixPath(normalized).parts).resolve()
        return candidate if candidate.is_relative_to(source.resolve()) and candidate.is_file() else None

    @staticmethod
    def _html_preview(content: Content, source: Path | None) -> str | None:
        body = ContentService._content_body(content.content_body)
        if not body and source and source.suffix.lower() in {".html", ".htm"}:
            try:
                body = source.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                return None
        if not body:
            return None
        if content.content_type == ContentType.DYNAMIC.value and "<html" not in body.lower():
            return f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'></head><body>{body}</body></html>"
        return body

    @staticmethod
    def list(
        db: Session, current_user: User, *, keyword: str | None, content_type: str | None,
        category: str | None, review_status: str | None, publish_status: str | None,
        created_by: int | None, page: int, page_size: int,
    ) -> PageResult[ContentRead]:
        scoped_user_id = None if current_user.role == "admin" else current_user.id
        items, total = ContentRepository.list(
            db, user_id=scoped_user_id, keyword=keyword, content_type=content_type, category=category,
            review_status=review_status, publish_status=publish_status, created_by=created_by,
            page=page, page_size=page_size,
        )
        return PageResult(items=[content_to_read(item) for item in items], total=total, page=page, page_size=page_size)

    @staticmethod
    def _get_model(db: Session, content_id: int) -> Content:
        content = ContentRepository.get_by_id(db, content_id)
        if not content:
            raise ResourceNotFound("内容不存在")
        return content

    @staticmethod
    def _ensure_view(content: Content, current_user: User) -> None:
        if current_user.role != "admin" and content.created_by != current_user.id and content.publish_status != PublishStatus.PUBLISHED.value:
            raise PermissionDenied("无权查看该内容")

    @classmethod
    def get(cls, db: Session, content_id: int, current_user: User) -> ContentRead:
        content = cls._get_model(db, content_id)
        cls._ensure_view(content, current_user)
        return content_to_read(content, include_body=True)

    @staticmethod
    def _validate_payload(
        db: Session, payload: ContentPayload, uploads: list[UploadFile], relative_paths: list[str],
        existing: Content | None = None,
    ) -> None:
        CategoryService.require_enabled(db, payload.category)
        target = PublishTargetRepository.get_by_id(db, payload.publish_target_id) if payload.publish_target_id else None
        PublishTargetService.validate_for_content(target, payload.content_type.value)
        has_existing_file = bool(existing and existing.source_file_path)
        if uploads:
            paths = relative_paths or [upload.filename or "" for upload in uploads]
            if relative_paths and len(relative_paths) != len(uploads):
                raise InvalidFileError("文件与相对路径数量不一致")
            is_directory = len(uploads) > 1 or any("/" in path.replace("\\", "/").strip("/") for path in paths)
            for upload, relative_path in zip(uploads, paths):
                validate_relative_upload_path(
                    relative_path or upload.filename or "", payload.content_type,
                    enforce_extension=not is_directory,
                )
        elif has_existing_file and existing:
            metadata = ContentService._source_metadata(existing)
            for item in metadata:
                validate_relative_upload_path(
                    str(item.get("relative_path") or item.get("name") or ""), payload.content_type,
                    enforce_extension=not existing.source_is_directory,
                )
        content_body = ContentService._content_body(payload.content_body)
        if not uploads and not has_existing_file and not content_body:
            raise InvalidFileError("请上传内容文件或填写页面内容")
        if payload.content_type == ContentType.DYNAMIC and not content_body:
            raise InvalidFileError("动态页面必须填写内容数据")

    @classmethod
    async def create(
        cls, db: Session, payload: ContentPayload, uploads: list[UploadFile], relative_paths: list[str],
        current_user: User,
    ) -> ContentRead:
        cls._validate_payload(db, payload, uploads, relative_paths)
        stored_path: str | None = None
        try:
            content = ContentRepository.create(
                db, title=payload.title, description=payload.description, category=payload.category,
                content_type=payload.content_type.value, content_body=cls._content_body(payload.content_body),
                publish_target_id=payload.publish_target_id, created_by=current_user.id,
            )
            if uploads:
                stored = await save_uploads(uploads, relative_paths, content.id, payload.content_type)
                stored_path = stored.path
                content.source_file_name = stored.display_name
                content.source_file_path = stored.path
                content.source_files = stored.files
                content.source_is_directory = stored.is_directory
            OperationLogRepository.create(db, user_id=current_user.id, action="create_content", target_type="content", target_id=content.id, message=f"创建内容 {content.title}")
            db.commit()
        except Exception:
            db.rollback()
            remove_source(stored_path)
            raise
        return content_to_read(cls._get_model(db, content.id), include_body=True)

    @classmethod
    async def update(
        cls, db: Session, content_id: int, payload: ContentPayload, uploads: list[UploadFile],
        relative_paths: list[str], current_user: User,
    ) -> ContentRead:
        content = cls._get_model(db, content_id)
        if current_user.role != "admin" and content.created_by != current_user.id:
            raise PermissionDenied("只能编辑自己创建的内容")
        if content.publish_status == PublishStatus.PUBLISHING.value:
            raise BusinessRuleError("内容正在发布，暂不能编辑")
        if current_user.role != "admin" and content.review_status not in {ReviewStatus.DRAFT.value, ReviewStatus.REJECTED.value}:
            raise BusinessRuleError("当前审核状态不允许编辑")
        cls._validate_payload(db, payload, uploads, relative_paths, content)
        old_path = content.source_file_path
        new_path: str | None = None
        try:
            content.title = payload.title
            content.description = payload.description
            content.category = payload.category
            content.content_type = payload.content_type.value
            content.publish_target_id = payload.publish_target_id
            content.content_body = cls._content_body(payload.content_body)
            content.updated_at = utc_now()
            if uploads:
                stored = await save_uploads(uploads, relative_paths, content.id, payload.content_type)
                new_path = stored.path
                content.source_file_name = stored.display_name
                content.source_file_path = stored.path
                content.source_files = stored.files
                content.source_is_directory = stored.is_directory
            OperationLogRepository.create(db, user_id=current_user.id, action="update_content", target_type="content", target_id=content.id, message=f"更新内容 {content.title}")
            db.commit()
        except Exception:
            db.rollback()
            remove_source(new_path)
            raise
        if new_path and old_path != new_path:
            remove_source(old_path)
        return content_to_read(cls._get_model(db, content.id), include_body=True)

    @classmethod
    def delete(cls, db: Session, content_id: int, current_user: User) -> None:
        content = cls._get_model(db, content_id)
        if current_user.role != "admin" and content.created_by != current_user.id:
            raise PermissionDenied("只能删除自己创建的内容")
        if content.publish_status == PublishStatus.PUBLISHING.value or content.review_status == ReviewStatus.PENDING.value:
            raise BusinessRuleError("当前状态不允许删除")
        if current_user.role != "admin" and content.publish_status == PublishStatus.PUBLISHED.value:
            raise BusinessRuleError("普通员工不能删除已发布内容")
        ContentRepository.soft_delete(content)
        OperationLogRepository.create(db, user_id=current_user.id, action="delete_content", target_type="content", target_id=content.id, message=f"逻辑删除内容 {content.title}")
        db.commit()

    @classmethod
    def submit(cls, db: Session, content_id: int, current_user: User) -> ContentRead:
        content = ContentRepository.get_for_update(db, content_id)
        if not content:
            raise ResourceNotFound("内容不存在")
        if current_user.role != "admin" and content.created_by != current_user.id:
            raise PermissionDenied("只能提交自己创建的内容")
        if content.review_status not in {ReviewStatus.DRAFT.value, ReviewStatus.REJECTED.value}:
            raise BusinessRuleError("仅草稿或已驳回内容可以提交")
        target = PublishTargetRepository.get_by_id(db, content.publish_target_id) if content.publish_target_id else None
        PublishTargetService.validate_for_content(target, content.content_type)
        from_status = content.review_status
        content.review_status = ReviewStatus.PENDING.value
        content.publish_status = PublishStatus.UNPUBLISHED.value
        content.reject_reason = None
        content.updated_at = utc_now()
        ReviewRepository.create_record(db, content_id=content.id, action=ReviewAction.SUBMIT.value, from_status=from_status, to_status=ReviewStatus.PENDING.value, comment="提交发布审核", operated_by=current_user.id)
        OperationLogRepository.create(db, user_id=current_user.id, action="submit_content", target_type="content", target_id=content.id, message=f"提交内容 {content.title} 审核")
        db.commit()
        return content_to_read(cls._get_model(db, content.id), include_body=True)

    @classmethod
    def preview(cls, db: Session, content_id: int, current_user: User) -> ContentPreview:
        content = cls._get_model(db, content_id)
        cls._ensure_view(content, current_user)
        source = cls._preview_source(content)
        metadata = cls._source_metadata(content)
        if source and (content.source_is_directory or len(metadata) > 1):
            files = [
                ContentPreviewFile(
                    name=str(item.get("name") or PurePosixPath(str(item.get("relative_path") or "")).name),
                    relative_path=str(item.get("relative_path") or item.get("name") or ""),
                    size=int(item["size"]) if item.get("size") is not None else None,
                    download_url=f"/contents/{content.id}/preview/files/{quote(str(item.get('relative_path') or item.get('name') or ''), safe='/')}",
                )
                for item in metadata
            ]
            return ContentPreview(preview_type="files", files=files)
        if content.content_type in {ContentType.HTML.value, ContentType.DYNAMIC.value}:
            page = cls._html_preview(content, source)
            if page:
                return ContentPreview(preview_type="text", content=page)
        if source and content.content_type == ContentType.IMAGE.value:
            return ContentPreview(preview_type="image", preview_url=f"/contents/{content.id}/preview/file")
        if source and content.content_type == ContentType.PDF.value:
            return ContentPreview(preview_type="pdf", preview_url=f"/contents/{content.id}/preview/file")
        if source and source.is_file() and content.content_type in {ContentType.WORD.value, ContentType.EXCEL.value}:
            document = build_document_preview(source, content.content_type)
            if document:
                return ContentPreview(preview_type="text", content=document)
        if content.source_file_name:
            try:
                size = source.stat().st_size if source else None
            except OSError:
                size = None
            return ContentPreview(
                preview_type="file", preview_url=f"/contents/{content.id}/preview/file" if source else None,
                file_name=content.source_file_name, file_size=size,
            )
        return ContentPreview(preview_type="unsupported")

    @classmethod
    def preview_file(cls, db: Session, content_id: int, current_user: User) -> tuple[Path, str]:
        content = cls._get_model(db, content_id)
        cls._ensure_view(content, current_user)
        source = cls._preview_source(content)
        if not source or not source.is_file():
            raise ResourceNotFound("预览源文件不存在")
        return source, content.source_file_name or source.name

    @classmethod
    def preview_source_file(
        cls, db: Session, content_id: int, relative_path: str, current_user: User,
    ) -> tuple[Path, str]:
        content = cls._get_model(db, content_id)
        cls._ensure_view(content, current_user)
        source = cls._source_entry(content, relative_path)
        if not source:
            raise ResourceNotFound("源文件不存在")
        return source, source.name

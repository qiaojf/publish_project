from pathlib import Path

from app.db.models.content import Content
from app.db.models.operation_log import OperationLog
from app.db.models.publish_record import PublishRecord
from app.db.models.review_record import ReviewRecord
from app.schemas.content import ContentFileRead, ContentRead
from app.schemas.publish_record import OperationLogRead, PublishRecordRead
from app.schemas.review import ReviewRecordRead


def _safe_size(path: str | None) -> int | None:
    if not path:
        return None
    try:
        file_path = Path(path)
        return file_path.stat().st_size if file_path.is_file() else None
    except OSError:
        return None


def content_to_read(content: Content, *, include_body: bool = False) -> ContentRead:
    submitted = max(
        (record.created_at for record in content.review_records if record.action == "submit"),
        default=None,
    )
    latest_publish = max(content.publish_records, key=lambda item: item.created_at, default=None)
    raw_files = content.source_files or []
    if not raw_files and content.source_file_name:
        raw_files = [{"name": content.source_file_name, "relative_path": content.source_file_name, "size": _safe_size(content.source_file_path)}]
    files = [ContentFileRead.model_validate(item) for item in raw_files]
    total_size = sum(item.size or 0 for item in files) or _safe_size(content.source_file_path)
    return ContentRead(
        id=content.id,
        title=content.title,
        description=content.description,
        category=content.category,
        content_type=content.content_type,
        file_name=content.source_file_name,
        file_size=total_size,
        files=files,
        source_is_directory=content.source_is_directory,
        content_body=content.content_body if include_body else None,
        created_by=content.created_by,
        creator_name=content.creator.name,
        creator_department=content.creator.department,
        created_at=content.created_at,
        updated_at=content.updated_at,
        submitted_at=submitted,
        review_status=content.review_status,
        publish_status=content.publish_status,
        publish_target_id=content.publish_target_id,
        publish_target_name=content.publish_target.name if content.publish_target else None,
        published_at=content.published_at,
        view_url=content.view_url,
        reject_reason=content.reject_reason,
        failure_reason=(
            latest_publish.error_message if latest_publish and latest_publish.status == "failed" else None
        ),
    )


def review_to_read(record: ReviewRecord) -> ReviewRecordRead:
    return ReviewRecordRead(
        id=record.id, content_id=record.content_id, action=record.action,
        from_status=record.from_status, to_status=record.to_status, comment=record.comment,
        operated_by=record.operated_by, operator_name=record.operator.name, created_at=record.created_at,
    )


def publish_record_to_read(record: PublishRecord) -> PublishRecordRead:
    return PublishRecordRead(
        id=record.id, content_id=record.content_id, content_title=record.content.title,
        content_type=record.content.content_type, publish_target_id=record.publish_target_id,
        target_name=record.publish_target.name, status=record.status, source_path=record.source_path,
        output_path=record.output_path, publish_url=record.publish_url, view_url=record.publish_url,
        message=record.message, error_message=record.error_message, failure_reason=record.error_message,
        triggered_by=record.triggered_by,
        triggered_by_name=record.triggered_by_user.name, started_at=record.started_at,
        finished_at=record.finished_at, created_at=record.created_at,
    )


def operation_log_to_read(log: OperationLog, *, target: str | None = None) -> OperationLogRead:
    resolved_target = target or (
        f"{log.target_type or 'system'} #{log.target_id}"
        if log.target_id else (log.target_type or "system")
    )
    return OperationLogRead(
        id=log.id, created_at=log.created_at, user_id=log.user_id,
        user_name=log.user.name if log.user else None, action=log.action,
        target_type=log.target_type, target_id=log.target_id, target=resolved_target,
        message=log.message, description=log.message, ip_address=log.ip_address,
    )

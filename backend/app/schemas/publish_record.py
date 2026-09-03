from datetime import datetime

from pydantic import BaseModel

from app.core.constants import ContentType, PublishRecordStatus


class PublishRecordRead(BaseModel):
    id: int
    content_id: int
    content_title: str
    content_type: ContentType
    publish_target_id: int
    target_name: str
    status: PublishRecordStatus
    source_path: str | None = None
    output_path: str | None = None
    publish_url: str | None = None
    view_url: str | None = None
    message: str | None = None
    error_message: str | None = None
    failure_reason: str | None = None
    triggered_by: int
    triggered_by_name: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime


class OperationLogRead(BaseModel):
    id: int
    created_at: datetime
    user_id: int | None
    user_name: str | None
    action: str
    target_type: str | None
    target_id: int | None
    target: str
    message: str | None
    description: str | None
    ip_address: str | None

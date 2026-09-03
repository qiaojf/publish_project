from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import ContentType, PublishStatus, ReviewStatus


class ContentPayload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    category: str | None = Field(default=None, max_length=100)
    content_type: ContentType
    publish_target_id: int | None = None
    content_body: str | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("标题不能为空")
        return value


class ContentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None = None
    category: str | None = None
    content_type: ContentType
    file_name: str | None = None
    file_size: int | None = None
    content_body: str | None = None
    created_by: int
    creator_name: str
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None
    review_status: ReviewStatus
    publish_status: PublishStatus
    publish_target_id: int | None = None
    publish_target_name: str | None = None
    published_at: datetime | None = None
    view_url: str | None = None
    reject_reason: str | None = None
    failure_reason: str | None = None


class ContentPreview(BaseModel):
    preview_type: str
    preview_url: str | None = None
    content: str | None = None
    file_name: str | None = None
    file_size: int | None = None

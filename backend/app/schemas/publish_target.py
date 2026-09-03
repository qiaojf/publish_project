from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import ContentType


class PublishTargetPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    content_types: list[ContentType] = Field(min_length=1)
    publish_root: str = Field(min_length=1, max_length=1000)
    base_url: str = Field(min_length=1, max_length=1000)
    enabled: bool = True

    @field_validator("name", "publish_root", "base_url")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("content_types")
    @classmethod
    def unique_types(cls, value: list[ContentType]) -> list[ContentType]:
        return list(dict.fromkeys(value))


class PublishTargetStatusUpdate(BaseModel):
    enabled: bool


class PublishTargetEmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    content_types: list[ContentType]
    enabled: bool
    created_at: datetime


class PublishTargetAdminRead(PublishTargetEmployeeRead):
    publish_root: str
    base_url: str
    created_by: int
    updated_at: datetime

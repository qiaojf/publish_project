from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ReviewAction
from app.schemas.content import ContentRead
from app.schemas.publish_target import PublishTargetAdminRead


class ReviewComment(BaseModel):
    comment: str = Field(default="审核通过", min_length=1, max_length=2000)


class RejectRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=2000)


class ReviewRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content_id: int
    action: ReviewAction
    from_status: str | None
    to_status: str
    comment: str | None
    operated_by: int
    operator_name: str
    created_at: datetime


class ReviewDetailRead(BaseModel):
    content: ContentRead
    publish_target: PublishTargetAdminRead | None
    history: list[ReviewRecordRead]

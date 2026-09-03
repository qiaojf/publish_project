from pydantic import BaseModel

from app.schemas.content import ContentRead


class DashboardRead(BaseModel):
    content_total: int | None = None
    my_content_total: int | None = None
    pending_review: int
    published: int
    publish_failed: int | None = None
    rejected: int | None = None
    recent_submissions: list[ContentRead]
    recent_contents: list[ContentRead] | None = None
    recent_publishes: list[ContentRead]

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Identity, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ContentType, PublishStatus, ReviewStatus
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.publish_record import PublishRecord
    from app.db.models.publish_target import PublishTarget
    from app.db.models.review_record import ReviewRecord
    from app.db.models.user import User


class Content(TimestampMixin, Base):
    __tablename__ = "contents"
    __table_args__ = (
        CheckConstraint("content_type IN ('html','dynamic','ppt','pdf','word','excel','image','file')", name="content_type_allowed"),
        CheckConstraint("review_status IN ('draft','pending','approved','rejected')", name="review_status_allowed"),
        CheckConstraint("publish_status IN ('unpublished','publishing','published','failed')", name="publish_status_allowed"),
        Index("ix_contents_created_by", "created_by"), Index("ix_contents_content_type", "content_type"),
        Index("ix_contents_category", "category"), Index("ix_contents_review_status", "review_status"),
        Index("ix_contents_publish_status", "publish_status"), Index("ix_contents_published_at", "published_at"),
        Index("ix_contents_publish_target_id", "publish_target_id"), Index("ix_contents_deleted_at", "deleted_at"),
        Index("ix_contents_review_publish", "review_status", "publish_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_file_name: Mapped[str | None] = mapped_column(String(255))
    source_file_path: Mapped[str | None] = mapped_column(String(1000))
    source_files: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False,
    )
    source_is_directory: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    content_body: Mapped[str | None] = mapped_column(Text)
    publish_target_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("publish_targets.id", ondelete="RESTRICT"))
    review_status: Mapped[str] = mapped_column(String(20), default=ReviewStatus.DRAFT.value, server_default="draft", nullable=False)
    publish_status: Mapped[str] = mapped_column(String(20), default=PublishStatus.UNPUBLISHED.value, server_default="unpublished", nullable=False)
    reject_reason: Mapped[str | None] = mapped_column(Text)
    view_url: Mapped[str | None] = mapped_column(String(1000))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    creator: Mapped["User"] = relationship(back_populates="contents", foreign_keys=[created_by])
    publish_target: Mapped["PublishTarget | None"] = relationship(back_populates="contents")
    review_records: Mapped[list["ReviewRecord"]] = relationship(back_populates="content", order_by="ReviewRecord.created_at")
    publish_records: Mapped[list["PublishRecord"]] = relationship(back_populates="content", order_by="PublishRecord.created_at")

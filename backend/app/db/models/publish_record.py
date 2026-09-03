from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utc_now

if TYPE_CHECKING:
    from app.db.models.content import Content
    from app.db.models.publish_target import PublishTarget
    from app.db.models.user import User


class PublishRecord(Base):
    __tablename__ = "publish_records"
    __table_args__ = (
        CheckConstraint("status IN ('publishing','success','failed')", name="status_allowed"),
        Index("ix_publish_records_content_id", "content_id"), Index("ix_publish_records_publish_target_id", "publish_target_id"),
        Index("ix_publish_records_status", "status"), Index("ix_publish_records_triggered_by", "triggered_by"),
        Index("ix_publish_records_created_at", "created_at"), Index("ix_publish_records_content_created", "content_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    content_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("contents.id", ondelete="RESTRICT"), nullable=False)
    publish_target_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("publish_targets.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    source_path: Mapped[str | None] = mapped_column(String(1000))
    output_path: Mapped[str | None] = mapped_column(String(1000))
    publish_url: Mapped[str | None] = mapped_column(String(1000))
    message: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    triggered_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False,
    )

    content: Mapped["Content"] = relationship(back_populates="publish_records")
    publish_target: Mapped["PublishTarget"] = relationship(back_populates="publish_records")
    triggered_by_user: Mapped["User"] = relationship(back_populates="publish_records")

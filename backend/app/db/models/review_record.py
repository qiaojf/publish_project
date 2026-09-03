from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utc_now

if TYPE_CHECKING:
    from app.db.models.content import Content
    from app.db.models.user import User


class ReviewRecord(Base):
    __tablename__ = "review_records"
    __table_args__ = (
        CheckConstraint("action IN ('submit','approve','reject')", name="action_allowed"),
        Index("ix_review_records_content_id", "content_id"), Index("ix_review_records_action", "action"),
        Index("ix_review_records_operated_by", "operated_by"), Index("ix_review_records_created_at", "created_at"),
        Index("ix_review_records_content_created", "content_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    content_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("contents.id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    operated_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False,
    )

    content: Mapped["Content"] = relationship(back_populates="review_records")
    operator: Mapped["User"] = relationship(back_populates="review_records")

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.content import Content
    from app.db.models.publish_record import PublishRecord
    from app.db.models.user import User


class PublishTarget(TimestampMixin, Base):
    __tablename__ = "publish_targets"
    __table_args__ = (Index("ix_publish_targets_enabled", "enabled"), Index("ix_publish_targets_created_by", "created_by"))

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    content_types: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    publish_root: Mapped[str] = mapped_column(String(1000), nullable=False)
    base_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    creator: Mapped["User"] = relationship(back_populates="publish_targets")
    contents: Mapped[list["Content"]] = relationship(back_populates="publish_target")
    publish_records: Mapped[list["PublishRecord"]] = relationship(back_populates="publish_target")

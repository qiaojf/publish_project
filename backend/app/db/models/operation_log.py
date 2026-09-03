from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utc_now

if TYPE_CHECKING:
    from app.db.models.user import User


class OperationLog(Base):
    __tablename__ = "operation_logs"
    __table_args__ = (
        Index("ix_operation_logs_user_id", "user_id"), Index("ix_operation_logs_action", "action"),
        Index("ix_operation_logs_target", "target_type", "target_id"), Index("ix_operation_logs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50))
    target_id: Mapped[int | None] = mapped_column(BigInteger)
    message: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False,
    )

    user: Mapped["User | None"] = relationship(back_populates="operation_logs")

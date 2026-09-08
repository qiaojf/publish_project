from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Identity, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import UserRole, UserStatus
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.content import Content
    from app.db.models.operation_log import OperationLog
    from app.db.models.publish_record import PublishRecord
    from app.db.models.publish_target import PublishTarget
    from app.db.models.review_record import ReviewRecord


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'employee')", name="role_allowed"),
        CheckConstraint("status IN ('active', 'disabled')", name="status_allowed"),
        Index("ix_users_role", "role"),
        Index("ix_users_status", "status"),
        Index("ix_users_deleted_at", "deleted_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), index=True)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.EMPLOYEE.value, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=UserStatus.ACTIVE.value, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    contents: Mapped[list["Content"]] = relationship(back_populates="creator", foreign_keys="Content.created_by")
    publish_targets: Mapped[list["PublishTarget"]] = relationship(back_populates="creator")
    review_records: Mapped[list["ReviewRecord"]] = relationship(back_populates="operator")
    publish_records: Mapped[list["PublishRecord"]] = relationship(back_populates="triggered_by_user")
    operation_logs: Mapped[list["OperationLog"]] = relationship(back_populates="user")

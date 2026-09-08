from sqlalchemy import BigInteger, Boolean, CheckConstraint, Identity, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import CategoryVisibility
from app.db.base import Base, TimestampMixin


class Category(TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("visibility_scope IN ('publisher', 'department', 'all')", name="visibility_scope_allowed"),
        CheckConstraint(
            "visibility_scope != 'department' OR (department IS NOT NULL AND btrim(department) != '')",
            name="visibility_department_required",
        ),
        Index("ix_categories_enabled_sort", "enabled", "sort_order"),
        Index("ix_categories_visibility_department", "visibility_scope", "department"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    visibility_scope: Mapped[str] = mapped_column(
        String(20), default=CategoryVisibility.ALL.value, server_default=CategoryVisibility.ALL.value, nullable=False,
    )
    department: Mapped[str | None] = mapped_column(String(100))

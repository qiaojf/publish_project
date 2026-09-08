"""Add department-based content visibility.

Revision ID: 20260908_0005
Revises: 20260907_0004
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260908_0005"
down_revision: str | None = "20260907_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("department", sa.String(length=100), nullable=True))
    op.create_index("ix_users_department", "users", ["department"])

    op.add_column(
        "categories",
        sa.Column("visibility_scope", sa.String(length=20), server_default="all", nullable=False),
    )
    op.add_column("categories", sa.Column("department", sa.String(length=100), nullable=True))
    op.create_check_constraint(
        "visibility_scope_allowed",
        "categories",
        "visibility_scope IN ('publisher', 'department', 'all')",
    )
    op.create_check_constraint(
        "visibility_department_required",
        "categories",
        "visibility_scope != 'department' OR (department IS NOT NULL AND btrim(department) != '')",
    )
    op.create_index(
        "ix_categories_visibility_department",
        "categories",
        ["visibility_scope", "department"],
    )


def downgrade() -> None:
    op.drop_index("ix_categories_visibility_department", table_name="categories")
    op.drop_constraint("visibility_department_required", "categories", type_="check")
    op.drop_constraint("visibility_scope_allowed", "categories", type_="check")
    op.drop_column("categories", "department")
    op.drop_column("categories", "visibility_scope")
    op.drop_index("ix_users_department", table_name="users")
    op.drop_column("users", "department")

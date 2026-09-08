"""Add configurable departments.

Revision ID: 20260908_0006
Revises: 20260908_0005
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260908_0006"
down_revision: str | None = "20260908_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_departments")),
        sa.UniqueConstraint("name", name=op.f("uq_departments_name")),
    )
    op.create_index("ix_departments_enabled_sort", "departments", ["enabled", "sort_order"])
    op.execute("""
        INSERT INTO departments (name, enabled, sort_order)
        SELECT existing.name, true, (ROW_NUMBER() OVER (ORDER BY existing.name) * 10)::integer
        FROM (
            SELECT DISTINCT btrim(department) AS name
            FROM users
            WHERE department IS NOT NULL AND btrim(department) <> ''
            UNION
            SELECT DISTINCT btrim(department) AS name
            FROM categories
            WHERE department IS NOT NULL AND btrim(department) <> ''
        ) AS existing
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_index("ix_departments_enabled_sort", table_name="departments")
    op.drop_table("departments")

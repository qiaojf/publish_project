"""Add configurable content categories.

Revision ID: 20260904_0003
Revises: 20260903_0002
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260904_0003"
down_revision: str | None = "20260903_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
DEFAULT_CATEGORIES = ("制度规范", "产品资料", "销售方案", "培训材料", "品牌素材", "公共资源")


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("name", name=op.f("uq_categories_name")),
    )
    op.create_index("ix_categories_enabled_sort", "categories", ["enabled", "sort_order"])
    categories = sa.table("categories", sa.column("name", sa.String()), sa.column("enabled", sa.Boolean()), sa.column("sort_order", sa.Integer()))
    op.bulk_insert(categories, [{"name": name, "enabled": True, "sort_order": index * 10} for index, name in enumerate(DEFAULT_CATEGORIES, start=1)])
    op.execute("""
        INSERT INTO categories (name, enabled, sort_order)
        SELECT existing.name, true, (1000 + ROW_NUMBER() OVER (ORDER BY existing.name) * 10)::integer
        FROM (SELECT DISTINCT category AS name FROM contents WHERE category IS NOT NULL AND btrim(category) <> '') AS existing
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_index("ix_categories_enabled_sort", table_name="categories")
    op.drop_table("categories")

"""Create the six PostgreSQL MVP tables.

Revision ID: 20260902_0001
Revises: None
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260902_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("role IN ('admin', 'employee')", name="role_allowed"),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="status_allowed"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_status", "users", ["status"])
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])

    op.create_table(
        "publish_targets",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("content_types", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("publish_root", sa.String(1000), nullable=False),
        sa.Column("base_url", sa.String(1000), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_publish_targets_created_by_users", ondelete="RESTRICT"),
    )
    op.create_index("ix_publish_targets_enabled", "publish_targets", ["enabled"])
    op.create_index("ix_publish_targets_created_by", "publish_targets", ["created_by"])

    op.create_table(
        "contents",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(100)),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("source_file_name", sa.String(255)),
        sa.Column("source_file_path", sa.String(1000)),
        sa.Column("content_body", sa.Text()),
        sa.Column("publish_target_id", sa.BigInteger()),
        sa.Column("review_status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("publish_status", sa.String(20), server_default="unpublished", nullable=False),
        sa.Column("reject_reason", sa.Text()),
        sa.Column("view_url", sa.String(1000)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("content_type IN ('html','dynamic','ppt','pdf','word','excel','image','file')", name="content_type_allowed"),
        sa.CheckConstraint("review_status IN ('draft','pending','approved','rejected')", name="review_status_allowed"),
        sa.CheckConstraint("publish_status IN ('unpublished','publishing','published','failed')", name="publish_status_allowed"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_contents_created_by_users", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["publish_target_id"], ["publish_targets.id"], name="fk_contents_publish_target_id_publish_targets", ondelete="RESTRICT"),
    )
    for name, columns in (
        ("ix_contents_created_by", ["created_by"]), ("ix_contents_content_type", ["content_type"]),
        ("ix_contents_category", ["category"]), ("ix_contents_review_status", ["review_status"]),
        ("ix_contents_publish_status", ["publish_status"]), ("ix_contents_published_at", ["published_at"]),
        ("ix_contents_publish_target_id", ["publish_target_id"]), ("ix_contents_deleted_at", ["deleted_at"]),
        ("ix_contents_review_publish", ["review_status", "publish_status"]),
    ):
        op.create_index(name, "contents", columns)

    op.create_table(
        "review_records",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("content_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("from_status", sa.String(20)),
        sa.Column("to_status", sa.String(20), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column("operated_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("action IN ('submit','approve','reject')", name="action_allowed"),
        sa.ForeignKeyConstraint(["content_id"], ["contents.id"], name="fk_review_records_content_id_contents", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["operated_by"], ["users.id"], name="fk_review_records_operated_by_users", ondelete="RESTRICT"),
    )
    for name, columns in (
        ("ix_review_records_content_id", ["content_id"]), ("ix_review_records_action", ["action"]),
        ("ix_review_records_operated_by", ["operated_by"]), ("ix_review_records_created_at", ["created_at"]),
        ("ix_review_records_content_created", ["content_id", "created_at"]),
    ):
        op.create_index(name, "review_records", columns)

    op.create_table(
        "publish_records",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("content_id", sa.BigInteger(), nullable=False),
        sa.Column("publish_target_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("source_path", sa.String(1000)),
        sa.Column("output_path", sa.String(1000)),
        sa.Column("publish_url", sa.String(1000)),
        sa.Column("message", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("triggered_by", sa.BigInteger(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("status IN ('publishing','success','failed')", name="status_allowed"),
        sa.ForeignKeyConstraint(["content_id"], ["contents.id"], name="fk_publish_records_content_id_contents", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["publish_target_id"], ["publish_targets.id"], name="fk_publish_records_publish_target_id_publish_targets", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["triggered_by"], ["users.id"], name="fk_publish_records_triggered_by_users", ondelete="RESTRICT"),
    )
    for name, columns in (
        ("ix_publish_records_content_id", ["content_id"]), ("ix_publish_records_publish_target_id", ["publish_target_id"]),
        ("ix_publish_records_status", ["status"]), ("ix_publish_records_triggered_by", ["triggered_by"]),
        ("ix_publish_records_created_at", ["created_at"]), ("ix_publish_records_content_created", ["content_id", "created_at"]),
    ):
        op.create_index(name, "publish_records", columns)

    op.create_table(
        "operation_logs",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("user_id", sa.BigInteger()),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50)),
        sa.Column("target_id", sa.BigInteger()),
        sa.Column("message", sa.Text()),
        sa.Column("ip_address", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_operation_logs_user_id_users", ondelete="RESTRICT"),
    )
    op.create_index("ix_operation_logs_user_id", "operation_logs", ["user_id"])
    op.create_index("ix_operation_logs_action", "operation_logs", ["action"])
    op.create_index("ix_operation_logs_target", "operation_logs", ["target_type", "target_id"])
    op.create_index("ix_operation_logs_created_at", "operation_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("operation_logs")
    op.drop_table("publish_records")
    op.drop_table("review_records")
    op.drop_table("contents")
    op.drop_table("publish_targets")
    op.drop_table("users")

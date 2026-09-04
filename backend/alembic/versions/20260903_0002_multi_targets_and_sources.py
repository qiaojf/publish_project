"""Add pluggable publish targets and multi-file source metadata.

Revision ID: 20260903_0002
Revises: 20260902_0001
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260903_0002"
down_revision: str | None = "20260902_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "publish_targets",
        sa.Column("target_type", sa.String(length=50), server_default="local", nullable=False),
    )
    op.add_column(
        "publish_targets",
        sa.Column(
            "config", postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"), nullable=False,
        ),
    )
    op.add_column("publish_targets", sa.Column("credential_ref", sa.String(length=255), nullable=True))
    op.alter_column("publish_targets", "publish_root", existing_type=sa.String(length=1000), nullable=True)
    op.alter_column("publish_targets", "base_url", existing_type=sa.String(length=1000), nullable=True)
    op.create_check_constraint(
        "target_type_allowed", "publish_targets",
        "target_type IN ('local','sftp','github','github_pages','onedrive','dropbox')",
    )
    op.create_index("ix_publish_targets_target_type", "publish_targets", ["target_type"])

    op.add_column(
        "contents",
        sa.Column(
            "source_files", postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"), nullable=False,
        ),
    )
    op.add_column(
        "contents",
        sa.Column("source_is_directory", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.execute(
        """
        UPDATE contents
        SET source_files = jsonb_build_array(
            jsonb_build_object(
                'name', source_file_name,
                'relative_path', source_file_name,
                'size', NULL
            )
        )
        WHERE source_file_name IS NOT NULL AND source_file_path IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_column("contents", "source_is_directory")
    op.drop_column("contents", "source_files")
    op.drop_index("ix_publish_targets_target_type", table_name="publish_targets")
    op.drop_constraint("target_type_allowed", "publish_targets", type_="check")
    op.alter_column("publish_targets", "base_url", existing_type=sa.String(length=1000), nullable=False)
    op.alter_column("publish_targets", "publish_root", existing_type=sa.String(length=1000), nullable=False)
    op.drop_column("publish_targets", "credential_ref")
    op.drop_column("publish_targets", "config")
    op.drop_column("publish_targets", "target_type")

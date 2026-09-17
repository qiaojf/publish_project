"""Add Instagram publish targets and video content.

Revision ID: 20260909_0008
Revises: 20260908_0007
"""
from collections.abc import Sequence

from alembic import op


revision: str = "20260909_0008"
down_revision: str | None = "20260908_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


CONTENT_TYPES_WITH_VIDEO = "content_type IN ('html','dynamic','ppt','pdf','word','excel','image','video','file')"
CONTENT_TYPES_WITHOUT_VIDEO = "content_type IN ('html','dynamic','ppt','pdf','word','excel','image','file')"
TARGET_TYPES_WITH_INSTAGRAM = "target_type IN ('local','sftp','github','github_pages','onedrive','dropbox','instagram')"
TARGET_TYPES_WITHOUT_INSTAGRAM = "target_type IN ('local','sftp','github','github_pages','onedrive','dropbox')"


def upgrade() -> None:
    op.drop_constraint(op.f("ck_contents_content_type_allowed"), "contents", type_="check")
    op.create_check_constraint("content_type_allowed", "contents", CONTENT_TYPES_WITH_VIDEO)
    op.drop_constraint(op.f("ck_publish_targets_target_type_allowed"), "publish_targets", type_="check")
    op.create_check_constraint("target_type_allowed", "publish_targets", TARGET_TYPES_WITH_INSTAGRAM)


def downgrade() -> None:
    op.drop_constraint(op.f("ck_publish_targets_target_type_allowed"), "publish_targets", type_="check")
    op.create_check_constraint("target_type_allowed", "publish_targets", TARGET_TYPES_WITHOUT_INSTAGRAM)
    op.drop_constraint(op.f("ck_contents_content_type_allowed"), "contents", type_="check")
    op.create_check_constraint("content_type_allowed", "contents", CONTENT_TYPES_WITHOUT_VIDEO)

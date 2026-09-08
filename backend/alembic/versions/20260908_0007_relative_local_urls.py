"""Normalize loopback Local publish URLs to site-relative URLs.

Revision ID: 20260908_0007
Revises: 20260908_0006
"""
from collections.abc import Sequence

from alembic import op


revision: str = "20260908_0007"
down_revision: str | None = "20260908_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


LOOPBACK_PREFIX = r"^https?://(localhost|127[.]0[.]0[.]1)(:[0-9]+)?"


def upgrade() -> None:
    op.execute(f"""
        UPDATE publish_targets
        SET base_url = regexp_replace(base_url, '{LOOPBACK_PREFIX}', '', 'i')
        WHERE target_type = 'local'
          AND base_url ~* '{LOOPBACK_PREFIX}/'
    """)
    op.execute(f"""
        UPDATE contents AS content
        SET view_url = regexp_replace(content.view_url, '{LOOPBACK_PREFIX}', '', 'i')
        FROM publish_targets AS target
        WHERE content.publish_target_id = target.id
          AND target.target_type = 'local'
          AND content.view_url ~* '{LOOPBACK_PREFIX}/'
    """)
    op.execute(f"""
        UPDATE publish_records AS record
        SET publish_url = regexp_replace(record.publish_url, '{LOOPBACK_PREFIX}', '', 'i')
        FROM publish_targets AS target
        WHERE record.publish_target_id = target.id
          AND target.target_type = 'local'
          AND record.publish_url ~* '{LOOPBACK_PREFIX}/'
    """)


def downgrade() -> None:
    # The original loopback hostname/port cannot be reconstructed safely.
    pass

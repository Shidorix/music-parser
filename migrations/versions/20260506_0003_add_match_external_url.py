"""Add external URL for persisted matches.

Revision ID: 20260506_0003
Revises: 20260506_0002
Create Date: 2026-05-06 23:40:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260506_0003"
down_revision = "20260506_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add optional public URL for best persisted match."""
    op.add_column(
        "playlist_items",
        sa.Column("match_external_url", sa.String(length=1024), nullable=True),
    )


def downgrade() -> None:
    """Drop optional public match URL."""
    op.drop_column("playlist_items", "match_external_url")

"""Create anonymous user session table.

Revision ID: 20260506_0002
Revises: 20260506_0001
Create Date: 2026-05-06 00:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260506_0002"
down_revision = "20260506_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user session table."""
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop user session table."""
    op.drop_table("user_sessions")

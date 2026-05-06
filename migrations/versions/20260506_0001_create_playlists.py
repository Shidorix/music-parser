"""Create playlist persistence tables.

Revision ID: 20260506_0001
Revises:
Create Date: 2026-05-06 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260506_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create playlist and playlist item tables."""
    op.create_table(
        "playlists",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_playlists_session_id"),
        "playlists",
        ["session_id"],
        unique=False,
    )

    op.create_table(
        "playlist_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("playlist_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("raw_input", sa.Text(), nullable=False),
        sa.Column("parsed_artist", sa.String(length=255), nullable=True),
        sa.Column("parsed_title", sa.String(length=255), nullable=True),
        sa.Column("parser_confidence", sa.Float(), nullable=False),
        sa.Column("match_track_id", sa.String(length=255), nullable=True),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("match_algorithm", sa.String(length=128), nullable=True),
        sa.Column("source", sa.String(length=128), nullable=True),
        sa.Column("is_uncertain", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["playlist_id"], ["playlists.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_playlist_items_playlist_id"),
        "playlist_items",
        ["playlist_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop playlist and playlist item tables."""
    op.drop_index(op.f("ix_playlist_items_playlist_id"), table_name="playlist_items")
    op.drop_table("playlist_items")
    op.drop_index(op.f("ix_playlists_session_id"), table_name="playlists")
    op.drop_table("playlists")

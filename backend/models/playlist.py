"""Playlist persistence models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class Playlist(Base):
    """Persisted playlist owned by an anonymous or authenticated session."""

    __tablename__ = "playlists"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    items: Mapped[list[PlaylistItem]] = relationship(
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistItem.position",
    )


class PlaylistItem(Base):
    """Persisted parsed and matched track item."""

    __tablename__ = "playlist_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    playlist_id: Mapped[UUID] = mapped_column(ForeignKey("playlists.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    raw_input: Mapped[str] = mapped_column(Text)
    parsed_artist: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parsed_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parser_confidence: Mapped[float] = mapped_column(Float)
    match_track_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_algorithm: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_uncertain: Mapped[bool] = mapped_column(default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    playlist: Mapped[Playlist] = relationship(back_populates="items")

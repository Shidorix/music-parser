"""CRUD operations for playlists."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import Playlist, PlaylistItem


class PlaylistItemCreate(BaseModel):
    """Input data for creating a playlist item."""

    model_config = ConfigDict(frozen=True)

    position: int = Field(ge=0)
    raw_input: str
    parsed_artist: str | None = None
    parsed_title: str | None = None
    parser_confidence: float = Field(ge=0.0, le=1.0)
    match_track_id: str | None = None
    match_external_url: str | None = None
    match_score: float | None = Field(default=None, ge=0.0, le=1.0)
    match_algorithm: str | None = None
    source: str | None = None
    is_uncertain: bool = True
    metadata_json: dict = Field(default_factory=dict)


class PlaylistCreate(BaseModel):
    """Input data for creating a playlist."""

    model_config = ConfigDict(frozen=True)

    session_id: str
    name: str | None = None
    items: tuple[PlaylistItemCreate, ...] = Field(default_factory=tuple)


class PlaylistItemReviewUpdate(BaseModel):
    """Input data for confirming or correcting a playlist item match."""

    model_config = ConfigDict(frozen=True)

    match_track_id: str = Field(min_length=1)
    match_external_url: str | None = None
    match_score: float = Field(ge=0.0, le=1.0)
    match_algorithm: str = Field(min_length=1)
    source: str = Field(min_length=1)
    is_uncertain: bool = False


class PlaylistCRUD:
    """CRUD helper for playlist persistence."""

    async def create(self, session: AsyncSession, data: PlaylistCreate) -> Playlist:
        """Create a playlist with optional items."""
        playlist = Playlist(session_id=data.session_id, name=data.name)
        playlist.items = [PlaylistItem(**item.model_dump()) for item in data.items]
        session.add(playlist)
        await session.flush()
        return playlist

    async def get_by_id(
        self,
        session: AsyncSession,
        playlist_id: UUID,
    ) -> Playlist | None:
        """Load one playlist by id with items."""
        result = await session.execute(
            select(Playlist)
            .options(selectinload(Playlist.items))
            .where(Playlist.id == playlist_id)
        )
        return result.scalar_one_or_none()

    async def list_by_session(
        self,
        session: AsyncSession,
        session_id: str,
    ) -> list[Playlist]:
        """List playlists for a session id."""
        result = await session.execute(
            select(Playlist)
            .options(selectinload(Playlist.items))
            .where(Playlist.session_id == session_id)
            .order_by(Playlist.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_name(
        self,
        session: AsyncSession,
        *,
        playlist_id: UUID,
        name: str | None,
    ) -> Playlist | None:
        """Update playlist display name."""
        playlist = await self.get_by_id(session, playlist_id)
        if playlist is None:
            return None
        playlist.name = name
        await session.flush()
        return playlist

    async def delete_by_id(
        self,
        session: AsyncSession,
        playlist_id: UUID,
    ) -> bool:
        """Delete one playlist by id."""
        playlist = await self.get_by_id(session, playlist_id)
        if playlist is None:
            return False
        await session.delete(playlist)
        await session.flush()
        return True

    async def delete_item(
        self,
        session: AsyncSession,
        *,
        playlist_id: UUID,
        item_id: UUID,
    ) -> bool:
        """Delete one playlist item by id."""
        result = await session.execute(
            delete(PlaylistItem).where(
                PlaylistItem.id == item_id,
                PlaylistItem.playlist_id == playlist_id,
            )
        )
        return result.rowcount > 0

    async def update_item_review(
        self,
        session: AsyncSession,
        *,
        playlist_id: UUID,
        item_id: UUID,
        data: PlaylistItemReviewUpdate,
    ) -> PlaylistItem | None:
        """Update an item after manual review."""
        result = await session.execute(
            select(PlaylistItem).where(
                PlaylistItem.id == item_id,
                PlaylistItem.playlist_id == playlist_id,
            )
        )
        item = result.scalar_one_or_none()
        if item is None:
            return None

        item.match_track_id = data.match_track_id
        item.match_external_url = data.match_external_url
        item.match_score = data.match_score
        item.match_algorithm = data.match_algorithm
        item.source = data.source
        item.is_uncertain = data.is_uncertain
        item.metadata_json = {
            **(item.metadata_json or {}),
            "manual_review": data.model_dump(mode="json"),
        }
        await session.flush()
        return item

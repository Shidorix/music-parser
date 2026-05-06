"""Service for persisting parse-and-match results as playlists."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud import (
    PlaylistCRUD,
    PlaylistCreate,
    PlaylistItemCreate,
    PlaylistItemReviewUpdate,
)
from backend.core.exceptions import AppException
from backend.core.services.schemas import (
    DeletedResourceResult,
    ParseAndMatchItemResult,
    ParseAndMatchResult,
    PersistedPlaylistItemResult,
    PersistedPlaylistResult,
)
from backend.models import Playlist, PlaylistItem


class PlaylistPersistenceService:
    """Persist parse-and-match output into playlist tables."""

    def __init__(self, playlist_crud: PlaylistCRUD | None = None) -> None:
        self._playlist_crud = playlist_crud or PlaylistCRUD()

    async def persist_parse_and_match_result(
        self,
        session: AsyncSession,
        *,
        session_id: str,
        name: str | None,
        parse_and_match_result: ParseAndMatchResult,
    ) -> PersistedPlaylistResult:
        """Create a playlist from a parse-and-match result."""
        playlist = await self._playlist_crud.create(
            session,
            PlaylistCreate(
                session_id=session_id,
                name=name,
                items=tuple(
                    self._build_item_create(position, item)
                    for position, item in enumerate(parse_and_match_result.items)
                ),
            ),
        )

        return PersistedPlaylistResult(
            playlist_id=playlist.id,
            session_id=playlist.session_id,
            name=playlist.name,
            created_at=playlist.created_at,
            total_items=len(playlist.items),
            uncertain_count=parse_and_match_result.uncertain_count,
            items=tuple(self._build_item_result(item) for item in playlist.items),
            explanation="Persisted parse-and-match result as a playlist.",
        )

    async def get_playlist(
        self,
        session: AsyncSession,
        playlist_id: UUID,
    ) -> PersistedPlaylistResult:
        """Load a persisted playlist by id."""
        playlist = await self._playlist_crud.get_by_id(session, playlist_id)
        if playlist is None:
            raise AppException(
                code="PLAYLIST_NOT_FOUND",
                message="Playlist was not found.",
                status_code=404,
            )
        return self._build_result(
            playlist,
            explanation="Loaded persisted playlist.",
        )

    async def list_playlists_by_session(
        self,
        session: AsyncSession,
        session_id: str,
    ) -> tuple[PersistedPlaylistResult, ...]:
        """List persisted playlists owned by a session."""
        playlists = await self._playlist_crud.list_by_session(session, session_id)
        return tuple(
            self._build_result(
                playlist,
                explanation="Loaded persisted playlist.",
            )
            for playlist in playlists
        )

    async def update_playlist_name(
        self,
        session: AsyncSession,
        playlist_id: UUID,
        name: str | None,
    ) -> PersistedPlaylistResult:
        """Update playlist display name."""
        playlist = await self._playlist_crud.update_name(
            session,
            playlist_id=playlist_id,
            name=name,
        )
        if playlist is None:
            raise self._playlist_not_found()
        return self._build_result(
            playlist,
            explanation="Updated persisted playlist name.",
        )

    async def delete_playlist(
        self,
        session: AsyncSession,
        playlist_id: UUID,
    ) -> DeletedResourceResult:
        """Delete one persisted playlist."""
        was_deleted = await self._playlist_crud.delete_by_id(session, playlist_id)
        if not was_deleted:
            raise self._playlist_not_found()
        return DeletedResourceResult(
            resource_id=playlist_id,
            resource_type="playlist",
            deleted=True,
            explanation="Deleted persisted playlist.",
        )

    async def delete_playlist_item(
        self,
        session: AsyncSession,
        *,
        playlist_id: UUID,
        item_id: UUID,
    ) -> PersistedPlaylistResult:
        """Delete one persisted playlist item and return the updated playlist."""
        was_deleted = await self._playlist_crud.delete_item(
            session,
            playlist_id=playlist_id,
            item_id=item_id,
        )
        if not was_deleted:
            raise AppException(
                code="PLAYLIST_ITEM_NOT_FOUND",
                message="Playlist item was not found.",
                status_code=404,
            )

        playlist = await self._playlist_crud.get_by_id(session, playlist_id)
        if playlist is None:
            raise self._playlist_not_found()
        return self._build_result(
            playlist,
            explanation="Deleted persisted playlist item.",
        )

    async def update_item_review(
        self,
        session: AsyncSession,
        *,
        playlist_id: UUID,
        item_id: UUID,
        match_track_id: str,
        match_score: float,
        match_algorithm: str,
        source: str,
        is_uncertain: bool,
    ) -> PersistedPlaylistItemResult:
        """Persist a manual review decision for one playlist item."""
        item = await self._playlist_crud.update_item_review(
            session,
            playlist_id=playlist_id,
            item_id=item_id,
            data=PlaylistItemReviewUpdate(
                match_track_id=match_track_id,
                match_score=match_score,
                match_algorithm=match_algorithm,
                source=source,
                is_uncertain=is_uncertain,
            ),
        )
        if item is None:
            raise AppException(
                code="PLAYLIST_ITEM_NOT_FOUND",
                message="Playlist item was not found.",
                status_code=404,
            )
        return self._build_item_result(item)

    def _build_item_create(
        self,
        position: int,
        item: ParseAndMatchItemResult,
    ) -> PlaylistItemCreate:
        best_match = item.match_result.matches[0] if item.match_result.matches else None

        return PlaylistItemCreate(
            position=position,
            raw_input=item.parsed_track.raw_input,
            parsed_artist=item.parsed_track.artist,
            parsed_title=item.parsed_track.title,
            parser_confidence=item.parsed_track.confidence,
            match_track_id=best_match.track_id if best_match is not None else None,
            match_score=best_match.score if best_match is not None else None,
            match_algorithm=best_match.algorithm if best_match is not None else None,
            source=best_match.source if best_match is not None else None,
            is_uncertain=item.is_uncertain,
            metadata_json=self._build_metadata(item),
        )

    def _build_metadata(self, item: ParseAndMatchItemResult) -> dict:
        return {
            "parsed_track": item.parsed_track.model_dump(mode="json"),
            "query_variants": [
                variant.model_dump(mode="json")
                for variant in item.match_result.query_variants
            ],
            "source_reports": [
                report.model_dump(mode="json") for report in item.source_reports
            ],
            "explanation": item.explanation,
        }

    def _build_result(
        self,
        playlist: Playlist,
        *,
        explanation: str,
    ) -> PersistedPlaylistResult:
        return PersistedPlaylistResult(
            playlist_id=playlist.id,
            session_id=playlist.session_id,
            name=playlist.name,
            created_at=playlist.created_at,
            total_items=len(playlist.items),
            uncertain_count=sum(item.is_uncertain for item in playlist.items),
            items=tuple(self._build_item_result(item) for item in playlist.items),
            explanation=explanation,
        )

    def _build_item_result(self, item: PlaylistItem) -> PersistedPlaylistItemResult:
        return PersistedPlaylistItemResult(
            item_id=item.id,
            position=item.position,
            raw_input=item.raw_input,
            parsed_artist=item.parsed_artist,
            parsed_title=item.parsed_title,
            parser_confidence=item.parser_confidence,
            match_track_id=item.match_track_id,
            match_score=item.match_score,
            match_algorithm=item.match_algorithm,
            source=item.source,
            is_uncertain=item.is_uncertain,
        )

    def _playlist_not_found(self) -> AppException:
        return AppException(
            code="PLAYLIST_NOT_FOUND",
            message="Playlist was not found.",
            status_code=404,
        )

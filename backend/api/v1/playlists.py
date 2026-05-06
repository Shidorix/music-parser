"""Playlist API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.dependencies import (
    get_parse_and_match_service,
    get_playlist_analytics_service,
    get_playlist_export_service,
    get_playlist_persistence_service,
)
from backend.core.analytics import PlaylistAnalyticsService, PlaylistStatsResult
from backend.core.export import (
    PlaylistExportFormat,
    PlaylistExportResult,
    PlaylistExportService,
)
from backend.core.services import (
    DeletedResourceResult,
    ParseAndMatchService,
    PersistedPlaylistItemResult,
    PersistedPlaylistResult,
    PlaylistPersistenceService,
)
from backend.database import get_db_session
from backend.schemas import APIMeta, APIResponse

router = APIRouter(prefix="/playlists", tags=["playlists"])


class CreatePlaylistFromLinesRequest(BaseModel):
    """Request body for creating a persisted playlist from raw lines."""

    model_config = ConfigDict(frozen=True)

    session_id: str = Field(
        min_length=1,
        description="Anonymous or authenticated owner session id.",
    )
    name: str | None = Field(default=None, description="Optional playlist name.")
    raw_lines: list[str] = Field(
        min_length=1,
        description="Raw track list lines to parse, match, and persist.",
    )
    match_limit: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum number of matches considered per input line.",
    )


class ReviewPlaylistItemRequest(BaseModel):
    """Request body for confirming or correcting a persisted match."""

    model_config = ConfigDict(frozen=True)

    match_track_id: str = Field(
        min_length=1,
        description="Track id selected during manual review.",
    )
    match_external_url: str | None = Field(
        default=None,
        description="Optional public URL for the manually selected track.",
    )
    match_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score assigned to the reviewed match.",
    )
    match_algorithm: str = Field(
        default="manual",
        min_length=1,
        description="Algorithm or review method that produced the correction.",
    )
    source: str = Field(
        default="manual",
        min_length=1,
        description="Source catalog for the selected match.",
    )
    is_uncertain: bool = Field(
        default=False,
        description="Whether the item should remain flagged for review.",
    )


class UpdatePlaylistRequest(BaseModel):
    """Request body for updating playlist metadata."""

    model_config = ConfigDict(frozen=True)

    name: str | None = Field(
        default=None,
        max_length=255,
        description="Updated playlist display name.",
    )


@router.post(
    "",
    response_model=APIResponse[PersistedPlaylistResult],
    summary="Create a persisted playlist from raw track lines.",
    description=(
        "Runs parse-and-match, persists the best match and parser metadata, and "
        "returns the created playlist id."
    ),
)
async def create_playlist_from_lines(
    request: CreatePlaylistFromLinesRequest,
    parse_and_match_service: Annotated[
        ParseAndMatchService,
        Depends(get_parse_and_match_service),
    ],
    persistence_service: Annotated[
        PlaylistPersistenceService,
        Depends(get_playlist_persistence_service),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> APIResponse[PersistedPlaylistResult]:
    """Create and persist a playlist from raw lines."""
    parse_and_match_result = await parse_and_match_service.parse_and_match(
        raw_lines=request.raw_lines,
        match_limit=request.match_limit,
    )
    persisted_playlist = await persistence_service.persist_parse_and_match_result(
        session,
        session_id=request.session_id,
        name=request.name,
        parse_and_match_result=parse_and_match_result,
    )
    await session.commit()

    return APIResponse(
        data=persisted_playlist,
        meta=APIMeta(total=persisted_playlist.total_items, page=0),
        error=None,
    )


@router.get(
    "/{playlist_id}",
    response_model=APIResponse[PersistedPlaylistResult],
    summary="Get a persisted playlist.",
    description="Loads a persisted playlist with parsed and matched item metadata.",
)
async def get_playlist(
    playlist_id: UUID,
    persistence_service: Annotated[
        PlaylistPersistenceService,
        Depends(get_playlist_persistence_service),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> APIResponse[PersistedPlaylistResult]:
    """Load one persisted playlist by id."""
    playlist = await persistence_service.get_playlist(session, playlist_id)
    return APIResponse(
        data=playlist,
        meta=APIMeta(total=playlist.total_items, page=0),
        error=None,
    )


@router.patch(
    "/{playlist_id}",
    response_model=APIResponse[PersistedPlaylistResult],
    summary="Update a persisted playlist.",
    description="Updates playlist metadata such as the display name.",
)
async def update_playlist(
    playlist_id: UUID,
    request: UpdatePlaylistRequest,
    persistence_service: Annotated[
        PlaylistPersistenceService,
        Depends(get_playlist_persistence_service),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> APIResponse[PersistedPlaylistResult]:
    """Update one persisted playlist."""
    playlist = await persistence_service.update_playlist_name(
        session,
        playlist_id,
        request.name,
    )
    await session.commit()
    return APIResponse(
        data=playlist,
        meta=APIMeta(total=playlist.total_items, page=0),
        error=None,
    )


@router.delete(
    "/{playlist_id}",
    response_model=APIResponse[DeletedResourceResult],
    summary="Delete a persisted playlist.",
    description="Deletes a playlist and its persisted items.",
)
async def delete_playlist(
    playlist_id: UUID,
    persistence_service: Annotated[
        PlaylistPersistenceService,
        Depends(get_playlist_persistence_service),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> APIResponse[DeletedResourceResult]:
    """Delete one persisted playlist."""
    deleted = await persistence_service.delete_playlist(session, playlist_id)
    await session.commit()
    return APIResponse(
        data=deleted,
        meta=APIMeta(total=1, page=0),
        error=None,
    )


@router.get(
    "/{playlist_id}/export",
    response_model=APIResponse[PlaylistExportResult],
    summary="Export a persisted playlist.",
    description="Serializes a persisted playlist into JSON, CSV, or M3U format.",
)
async def export_playlist(
    playlist_id: UUID,
    persistence_service: Annotated[
        PlaylistPersistenceService,
        Depends(get_playlist_persistence_service),
    ],
    export_service: Annotated[
        PlaylistExportService,
        Depends(get_playlist_export_service),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    export_format: Annotated[
        PlaylistExportFormat,
        Query(
            alias="format",
            description="Portable export format.",
        ),
    ] = PlaylistExportFormat.JSON,
) -> APIResponse[PlaylistExportResult]:
    """Export one persisted playlist."""
    playlist = await persistence_service.get_playlist(session, playlist_id)
    export_result = export_service.export_playlist(playlist, export_format)
    return APIResponse(
        data=export_result,
        meta=APIMeta(total=export_result.total_items, page=0),
        error=None,
    )


@router.get(
    "/{playlist_id}/stats",
    response_model=APIResponse[PlaylistStatsResult],
    summary="Get persisted playlist statistics.",
    description=(
        "Computes aggregate parser, matcher, source, algorithm, and manual-review "
        "metrics for one playlist."
    ),
)
async def get_playlist_stats(
    playlist_id: UUID,
    persistence_service: Annotated[
        PlaylistPersistenceService,
        Depends(get_playlist_persistence_service),
    ],
    analytics_service: Annotated[
        PlaylistAnalyticsService,
        Depends(get_playlist_analytics_service),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> APIResponse[PlaylistStatsResult]:
    """Compute aggregate quality metrics for one persisted playlist."""
    playlist = await persistence_service.get_playlist(session, playlist_id)
    stats = analytics_service.compute_stats(playlist)
    return APIResponse(
        data=stats,
        meta=APIMeta(total=stats.total_items, page=0),
        error=None,
    )


@router.get(
    "",
    response_model=APIResponse[tuple[PersistedPlaylistResult, ...]],
    summary="List persisted playlists for a session.",
    description="Loads persisted playlists owned by an anonymous or authenticated session.",
)
async def list_playlists(
    session_id: Annotated[
        str,
        Query(min_length=1, description="Anonymous or authenticated owner session id."),
    ],
    persistence_service: Annotated[
        PlaylistPersistenceService,
        Depends(get_playlist_persistence_service),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> APIResponse[tuple[PersistedPlaylistResult, ...]]:
    """List persisted playlists for a session."""
    playlists = await persistence_service.list_playlists_by_session(
        session,
        session_id,
    )
    return APIResponse(
        data=playlists,
        meta=APIMeta(total=len(playlists), page=0),
        error=None,
    )


@router.patch(
    "/{playlist_id}/items/{item_id}",
    response_model=APIResponse[PersistedPlaylistItemResult],
    summary="Review a persisted playlist item.",
    description=(
        "Confirms or corrects the best match for one playlist item and stores "
        "the manual review metadata."
    ),
)
async def review_playlist_item(
    playlist_id: UUID,
    item_id: UUID,
    request: ReviewPlaylistItemRequest,
    persistence_service: Annotated[
        PlaylistPersistenceService,
        Depends(get_playlist_persistence_service),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> APIResponse[PersistedPlaylistItemResult]:
    """Persist a manual review decision for one playlist item."""
    item = await persistence_service.update_item_review(
        session,
        playlist_id=playlist_id,
        item_id=item_id,
        match_track_id=request.match_track_id,
        match_external_url=request.match_external_url,
        match_score=request.match_score,
        match_algorithm=request.match_algorithm,
        source=request.source,
        is_uncertain=request.is_uncertain,
    )
    await session.commit()
    return APIResponse(
        data=item,
        meta=APIMeta(total=1, page=0),
        error=None,
    )


@router.delete(
    "/{playlist_id}/items/{item_id}",
    response_model=APIResponse[PersistedPlaylistResult],
    summary="Delete a persisted playlist item.",
    description="Deletes one playlist item and returns the updated playlist.",
)
async def delete_playlist_item(
    playlist_id: UUID,
    item_id: UUID,
    persistence_service: Annotated[
        PlaylistPersistenceService,
        Depends(get_playlist_persistence_service),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> APIResponse[PersistedPlaylistResult]:
    """Delete one persisted playlist item."""
    playlist = await persistence_service.delete_playlist_item(
        session,
        playlist_id=playlist_id,
        item_id=item_id,
    )
    await session.commit()
    return APIResponse(
        data=playlist,
        meta=APIMeta(total=playlist.total_items, page=0),
        error=None,
    )

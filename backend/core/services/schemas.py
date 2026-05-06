"""Pydantic schemas for composed core service results."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.core.matcher import ParsedTrackMatchResult
from backend.core.parser import ParsedTrack
from backend.core.search import TrackSearchSourceReport


class ParseLinesResult(BaseModel):
    """Parser-only response for multiple input lines."""

    model_config = ConfigDict(frozen=True)

    items: tuple[ParsedTrack, ...] = Field(description="Parsed track results.")
    total: int = Field(ge=0, description="Number of processed lines.")
    explanation: str = Field(description="Human-readable parser service summary.")


class UserSessionResult(BaseModel):
    """Anonymous user session response."""

    model_config = ConfigDict(frozen=True)

    session_id: UUID = Field(description="Anonymous user session id.")
    display_name: str | None = Field(description="Optional user-facing session label.")
    created_at: datetime = Field(description="Session creation timestamp.")
    last_seen_at: datetime = Field(description="Last seen timestamp.")
    explanation: str = Field(description="Human-readable session summary.")


class DeletedResourceResult(BaseModel):
    """Response for a successfully deleted resource."""

    model_config = ConfigDict(frozen=True)

    resource_id: UUID = Field(description="Deleted resource id.")
    resource_type: str = Field(description="Deleted resource type.")
    deleted: bool = Field(description="Whether the resource was deleted.")
    explanation: str = Field(description="Human-readable deletion summary.")


class ParseAndMatchItemResult(BaseModel):
    """Parse-and-match result for one input line."""

    model_config = ConfigDict(frozen=True)

    parsed_track: ParsedTrack = Field(description="Parsed track metadata.")
    match_result: ParsedTrackMatchResult = Field(
        description="Ranked matches for the parsed track."
    )
    source_reports: tuple[TrackSearchSourceReport, ...] = Field(
        default_factory=tuple,
        description="Candidate search source reports used for this item.",
    )
    best_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Best available match score, or 0 when no matches exist.",
    )
    is_uncertain: bool = Field(
        description="Whether the best match is below the confidence threshold."
    )
    explanation: str = Field(description="Human-readable uncertainty explanation.")


class ParseAndMatchResult(BaseModel):
    """End-to-end parse-and-match response for multiple input lines."""

    model_config = ConfigDict(frozen=True)

    items: tuple[ParseAndMatchItemResult, ...] = Field(
        description="Per-line parse-and-match results."
    )
    total: int = Field(ge=0, description="Number of processed non-empty lines.")
    uncertain_count: int = Field(ge=0, description="Number of uncertain results.")
    confidence_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="Configured threshold used to mark uncertain matches.",
    )
    explanation: str = Field(description="Human-readable service summary.")


class PersistedPlaylistItemResult(BaseModel):
    """Persisted playlist item response."""

    model_config = ConfigDict(frozen=True)

    item_id: UUID = Field(description="Persisted playlist item id.")
    position: int = Field(ge=0, description="Item position in the playlist.")
    raw_input: str = Field(description="Original input line.")
    parsed_artist: str | None = Field(description="Persisted parsed artist.")
    parsed_title: str | None = Field(description="Persisted parsed title.")
    parser_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Persisted parser confidence.",
    )
    match_track_id: str | None = Field(description="Persisted best match track id.")
    match_external_url: str | None = Field(
        default=None,
        description="Public URL for opening the persisted best match.",
    )
    match_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Persisted best match score.",
    )
    match_algorithm: str | None = Field(
        default=None,
        description="Matcher algorithm used for the persisted best match.",
    )
    source: str | None = Field(
        default=None,
        description="External or demo source that produced the persisted best match.",
    )
    is_uncertain: bool = Field(description="Whether this item needs review.")


class PersistedPlaylistResult(BaseModel):
    """Persisted playlist response."""

    model_config = ConfigDict(frozen=True)

    playlist_id: UUID = Field(description="Persisted playlist id.")
    session_id: str = Field(description="Owner session id.")
    name: str | None = Field(description="Playlist display name.")
    created_at: datetime = Field(description="Playlist creation timestamp.")
    total_items: int = Field(ge=0, description="Number of persisted items.")
    uncertain_count: int = Field(ge=0, description="Number of uncertain items.")
    items: tuple[PersistedPlaylistItemResult, ...] = Field(
        description="Persisted playlist items."
    )
    explanation: str = Field(description="Human-readable persistence summary.")

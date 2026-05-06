"""Schemas for aggregated track search results."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from backend.core.matcher import TrackCandidate


class TrackSearchSourceStatus(str, Enum):
    """Status of one search provider call."""

    SUCCESS = "success"
    FAILED = "failed"


class TrackSearchSourceReport(BaseModel):
    """Per-provider search metadata."""

    model_config = ConfigDict(frozen=True)

    source: str = Field(description="Provider source name.")
    status: TrackSearchSourceStatus = Field(description="Provider call status.")
    candidate_count: int = Field(ge=0, description="Number of returned candidates.")
    error_code: str | None = Field(default=None, description="Provider error code.")
    error_message: str | None = Field(
        default=None,
        description="Provider error message.",
    )


class TrackSearchResult(BaseModel):
    """Aggregated track search result."""

    model_config = ConfigDict(frozen=True)

    query: str = Field(description="Search query.")
    candidates: tuple[TrackCandidate, ...] = Field(
        description="Deduplicated track candidates from all providers."
    )
    source_reports: tuple[TrackSearchSourceReport, ...] = Field(
        description="Per-provider execution reports."
    )
    explanation: str = Field(description="Human-readable search summary.")

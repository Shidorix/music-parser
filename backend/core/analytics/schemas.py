"""Schemas for playlist analytics."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlaylistStatsResult(BaseModel):
    """Aggregated quality metrics for a persisted playlist."""

    model_config = ConfigDict(frozen=True)

    playlist_id: UUID = Field(description="Analyzed playlist id.")
    total_items: int = Field(ge=0, description="Number of playlist items.")
    uncertain_count: int = Field(ge=0, description="Items that still need review.")
    confirmed_count: int = Field(
        ge=0, description="Items accepted by confidence or review."
    )
    average_match_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Average score across scored matches.",
    )
    average_parser_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Average parser confidence across playlist items.",
    )
    source_counts: dict[str, int] = Field(description="Matched item count by source.")
    algorithm_counts: dict[str, int] = Field(
        description="Matched item count by matcher algorithm."
    )
    uncertain_positions: tuple[int, ...] = Field(
        description="Positions of items that still need manual review."
    )
    explanation: str = Field(description="Human-readable analytics summary.")

"""Pydantic schemas for fuzzy matching results."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TrackCandidate(BaseModel):
    """Candidate track record used by matching algorithms."""

    model_config = ConfigDict(frozen=True)

    track_id: str = Field(description="Stable track identifier from a source catalog.")
    artist: str | None = Field(default=None, description="Candidate artist name.")
    title: str = Field(description="Candidate track title.")
    source: str = Field(description="Candidate source, for example spotify or youtube.")
    external_url: str | None = Field(
        default=None,
        description="Optional public URL for opening the candidate in its source.",
    )

    @property
    def display_text(self) -> str:
        """Return the comparable artist-title text for matching."""
        if self.artist is None or self.artist.strip() == "":
            return self.title

        return f"{self.artist} - {self.title}"


class MatchQueryVariant(BaseModel):
    """One query variant generated from a parsed track."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(description="Query text sent to a matcher.")
    source: str = Field(
        description="Query source, for example parsed_fields or transliteration."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence of this query variant.",
    )
    explanation: str = Field(description="Human-readable reason for this query.")


class MatchResult(BaseModel):
    """Explainable result of matching a query against one candidate."""

    model_config = ConfigDict(frozen=True)

    track_id: str = Field(description="Matched candidate track identifier.")
    query: str = Field(description="Original query text used for matching.")
    candidate: TrackCandidate = Field(description="Candidate track that was scored.")
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Algorithm-specific normalized score from 0 to 1.",
    )
    algorithm: str = Field(description="Matching algorithm that produced the score.")
    source: str = Field(description="Source catalog for the matched candidate.")
    distance: int = Field(ge=0, description="Raw Levenshtein edit distance.")
    normalized_query: str = Field(description="Normalized query used by the matcher.")
    normalized_candidate: str = Field(
        description="Normalized candidate text used by the matcher."
    )
    explanation: str = Field(description="Human-readable reason for the score.")
    query_variant_source: str = Field(
        default="direct",
        description="Source of the query variant that produced this result.",
    )
    query_variant_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence of the query variant that produced this result.",
    )


class ParsedTrackMatchResult(BaseModel):
    """End-to-end matching result for one parsed track."""

    model_config = ConfigDict(frozen=True)

    parsed_track_raw_input: str = Field(description="Original parsed input line.")
    query_variants: tuple[MatchQueryVariant, ...] = Field(
        description="Query variants generated for matching."
    )
    matches: tuple[MatchResult, ...] = Field(description="Ranked deduplicated matches.")
    explanation: str = Field(description="Human-readable matching service summary.")

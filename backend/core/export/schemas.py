"""Schemas for playlist export results."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PlaylistExportFormat(StrEnum):
    """Supported playlist export formats."""

    JSON = "json"
    CSV = "csv"
    M3U = "m3u"


class PlaylistExportResult(BaseModel):
    """Serialized playlist export payload."""

    model_config = ConfigDict(frozen=True)

    filename: str = Field(description="Suggested export filename.")
    format: PlaylistExportFormat = Field(description="Serialized export format.")
    media_type: str = Field(description="HTTP media type for the export content.")
    content: str = Field(description="Serialized playlist content.")
    total_items: int = Field(ge=0, description="Number of exported playlist items.")
    explanation: str = Field(description="Human-readable export summary.")

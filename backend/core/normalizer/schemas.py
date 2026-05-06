"""Pydantic schemas for text normalization results."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class NormalizedText(BaseModel):
    """Result of normalizing one raw input string."""

    model_config = ConfigDict(frozen=True)

    raw_text: str = Field(description="Original input text before normalization.")
    normalized_text: str = Field(description="Normalized text used by NLP modules.")
    transformations: tuple[str, ...] = Field(
        description="Names of transformations applied during normalization."
    )

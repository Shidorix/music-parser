"""Pydantic schemas for transliteration metadata."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TransliterationDirection(str, Enum):
    """Supported transliteration directions."""

    CYRILLIC_TO_LATIN = "cyrillic_to_latin"
    LATIN_TO_CYRILLIC = "latin_to_cyrillic"


class TransliterationCandidate(BaseModel):
    """One rule-based transliteration candidate for matching experiments."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(description="Transliterated text candidate.")
    direction: TransliterationDirection = Field(
        description="Direction used to produce the candidate."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Rule-based confidence for this transliteration candidate.",
    )
    explanation: str = Field(description="Human-readable transliteration rationale.")


class TransliterationResult(BaseModel):
    """Result of generating transliteration candidates for one line."""

    model_config = ConfigDict(frozen=True)

    source_text: str = Field(description="Text used as transliteration input.")
    candidates: tuple[TransliterationCandidate, ...] = Field(
        description="Generated transliteration candidates."
    )
    explanation: str = Field(description="Summary of the transliteration decision.")

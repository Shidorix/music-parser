"""Pydantic schemas for parser results."""

from __future__ import annotations

from enum import Enum

from backend.core.language import DetectedLanguage
from backend.core.transliterator import TransliterationCandidate
from pydantic import BaseModel, ConfigDict, Field


class TrackPattern(str, Enum):
    """Supported parser pattern labels for experiments and explanations."""

    ARTIST_TITLE = "artist_title"
    TITLE_ARTIST = "title_artist"
    TITLE_ARTIST_PARENTHESIS = "title_artist_parenthesis"
    TITLE_ARTIST_BRACKETS = "title_artist_brackets"
    UNKNOWN = "unknown"


class SeparatorParseOrder(str, Enum):
    """Interpretation strategy for ambiguous separator-based patterns."""

    ARTIST_TITLE = "artist_title"
    TITLE_ARTIST = "title_artist"


class ParsedTrack(BaseModel):
    """Structured result of parsing one unstructured track line."""

    model_config = ConfigDict(frozen=True)

    raw_input: str = Field(description="Original user-provided input line.")
    normalized_input: str = Field(description="Parser-normalized input line.")
    artist: str | None = Field(default=None, description="Detected artist name.")
    title: str | None = Field(default=None, description="Detected track title.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Parser confidence score from 0 to 1.",
    )
    pattern: TrackPattern = Field(description="Pattern that produced this result.")
    explanation: str = Field(description="Human-readable reason for the result.")
    language: DetectedLanguage = Field(
        default=DetectedLanguage.UNKNOWN,
        description="Language detected after text normalization.",
    )
    language_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence of the language detection step.",
    )
    language_explanation: str = Field(
        default="Language detection was not run.",
        description="Human-readable reason for the detected language.",
    )
    normalization_steps: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Text normalization transformations applied before parsing.",
    )
    transliteration_candidates: tuple[TransliterationCandidate, ...] = Field(
        default_factory=tuple,
        description="Rule-based transliteration candidates for later matching.",
    )
    transliteration_explanation: str = Field(
        default="Transliteration was not run.",
        description="Human-readable summary of transliteration decisions.",
    )

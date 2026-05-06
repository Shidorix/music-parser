"""Pydantic schemas for language detection metadata."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DetectedLanguage(str, Enum):
    """Language labels used by the NLP pipeline."""

    EN = "en"
    RU = "ru"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class LanguageDetectionResult(BaseModel):
    """Explainable result of language detection for one normalized line."""

    model_config = ConfigDict(frozen=True)

    language: DetectedLanguage = Field(description="Detected language label.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Language detection confidence from 0 to 1.",
    )
    cyrillic_ratio: float = Field(
        ge=0.0,
        le=1.0,
        description="Share of Cyrillic letters among detected letters.",
    )
    latin_ratio: float = Field(
        ge=0.0,
        le=1.0,
        description="Share of Latin letters among detected letters.",
    )
    explanation: str = Field(description="Human-readable detection rationale.")

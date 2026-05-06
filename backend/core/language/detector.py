"""Transparent baseline language detection for track text."""

from __future__ import annotations

import re
from typing import Final

from backend.core.language.schemas import DetectedLanguage, LanguageDetectionResult

_CYRILLIC_RE: Final[re.Pattern[str]] = re.compile(r"[а-яё]", re.IGNORECASE)
_LATIN_RE: Final[re.Pattern[str]] = re.compile(r"[a-z]", re.IGNORECASE)


class LanguageDetector:
    """Detect whether normalized track text is Russian, English, or mixed."""

    def __init__(self, mixed_threshold: float = 0.2) -> None:
        if not 0.0 <= mixed_threshold <= 0.5:
            msg = "mixed_threshold must be between 0.0 and 0.5."
            raise ValueError(msg)
        self._mixed_threshold = mixed_threshold

    def detect(self, text: str) -> LanguageDetectionResult:
        """Detect language by comparing Cyrillic and Latin character ratios."""
        cyrillic_count = len(_CYRILLIC_RE.findall(text))
        latin_count = len(_LATIN_RE.findall(text))
        letter_count = cyrillic_count + latin_count

        if letter_count == 0:
            return LanguageDetectionResult(
                language=DetectedLanguage.UNKNOWN,
                confidence=0.0,
                cyrillic_ratio=0.0,
                latin_ratio=0.0,
                explanation="No Cyrillic or Latin letters were found.",
            )

        cyrillic_ratio = cyrillic_count / letter_count
        latin_ratio = latin_count / letter_count

        if cyrillic_count > 0 and latin_count > 0:
            minority_ratio = min(cyrillic_ratio, latin_ratio)
            if minority_ratio >= self._mixed_threshold:
                return LanguageDetectionResult(
                    language=DetectedLanguage.MIXED,
                    confidence=round(0.5 + minority_ratio, 4),
                    cyrillic_ratio=round(cyrillic_ratio, 4),
                    latin_ratio=round(latin_ratio, 4),
                    explanation=(
                        "Both Cyrillic and Latin letters exceed the mixed-language "
                        "threshold."
                    ),
                )

        if cyrillic_ratio >= latin_ratio:
            return LanguageDetectionResult(
                language=DetectedLanguage.RU,
                confidence=round(cyrillic_ratio, 4),
                cyrillic_ratio=round(cyrillic_ratio, 4),
                latin_ratio=round(latin_ratio, 4),
                explanation="Cyrillic letters dominate the normalized input.",
            )

        return LanguageDetectionResult(
            language=DetectedLanguage.EN,
            confidence=round(latin_ratio, 4),
            cyrillic_ratio=round(cyrillic_ratio, 4),
            latin_ratio=round(latin_ratio, 4),
            explanation="Latin letters dominate the normalized input.",
        )

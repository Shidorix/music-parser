"""Shared text normalization helpers for fuzzy matchers."""

from __future__ import annotations

import re
from typing import Final

_WHITESPACE_RE: Final[re.Pattern[str]] = re.compile(r"\s+")
_SEPARATORS_RE: Final[re.Pattern[str]] = re.compile(r"[_|/]+")
_BRACKETED_NOISE_RE: Final[re.Pattern[str]] = re.compile(
    r"\((?:[^)]*(?:official|video|lyrics?|audio|remaster(?:ed)?|visualizer|hd|4k)[^)]*)\)|"
    r"\[(?:[^\]]*(?:official|video|lyrics?|audio|remaster(?:ed)?|visualizer|hd|4k)[^\]]*)\]",
    re.IGNORECASE,
)
_NOISE_PHRASES_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:"
    r"official\s+music\s+video|"
    r"official\s+video|"
    r"official\s+audio|"
    r"lyric\s+video|"
    r"lyrics?|"
    r"music\s+video|"
    r"visualizer|"
    r"remaster(?:ed)?|"
    r"hd|"
    r"4k"
    r")\b",
    re.IGNORECASE,
)


def normalize_match_text(value: str) -> str:
    """Normalize a query or candidate string before fuzzy matching."""
    normalized_value = value.casefold().strip()
    normalized_value = _SEPARATORS_RE.sub(" ", normalized_value)
    normalized_value = _BRACKETED_NOISE_RE.sub(" ", normalized_value)
    normalized_value = _NOISE_PHRASES_RE.sub(" ", normalized_value)
    return _WHITESPACE_RE.sub(" ", normalized_value).strip()

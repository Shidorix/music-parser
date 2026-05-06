"""Fuzzy matching algorithms and contracts."""

from backend.core.matcher.base import BaseMatcher
from backend.core.matcher.hybrid import HybridMatcher
from backend.core.matcher.jaro_winkler import JaroWinklerMatcher
from backend.core.matcher.levenshtein import LevenshteinMatcher
from backend.core.matcher.schemas import (
    MatchQueryVariant,
    MatchResult,
    ParsedTrackMatchResult,
    TrackCandidate,
)
from backend.core.matcher.service import MatchingService

__all__ = [
    "BaseMatcher",
    "HybridMatcher",
    "JaroWinklerMatcher",
    "LevenshteinMatcher",
    "MatchQueryVariant",
    "MatchResult",
    "MatchingService",
    "ParsedTrackMatchResult",
    "TrackCandidate",
]

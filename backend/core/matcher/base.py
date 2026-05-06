"""Matcher interface shared by all matching algorithms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from backend.core.matcher.schemas import MatchResult, TrackCandidate


class BaseMatcher(ABC):
    """Common interface for swappable fuzzy matching algorithms."""

    algorithm_name: str

    @abstractmethod
    def match(
        self,
        query: str,
        candidates: Sequence[TrackCandidate],
        *,
        limit: int | None = None,
    ) -> list[MatchResult]:
        """Match a query string against candidate tracks."""

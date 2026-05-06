"""Levenshtein distance baseline matcher."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Final

from backend.core.matcher.base import BaseMatcher
from backend.core.matcher.schemas import MatchResult, TrackCandidate

_WHITESPACE_RE: Final[re.Pattern[str]] = re.compile(r"\s+")


class LevenshteinMatcher(BaseMatcher):
    """Rank candidates by normalized Levenshtein similarity."""

    algorithm_name = "levenshtein"

    def match(
        self,
        query: str,
        candidates: Sequence[TrackCandidate],
        *,
        limit: int | None = None,
    ) -> list[MatchResult]:
        """Match a query string against candidate tracks."""
        normalized_query = self._normalize(query)
        results = [
            self._match_candidate(
                query=query,
                normalized_query=normalized_query,
                candidate=candidate,
            )
            for candidate in candidates
        ]
        ranked_results = sorted(
            results,
            key=lambda result: (
                result.score,
                -result.distance,
                result.candidate.display_text,
            ),
            reverse=True,
        )

        if limit is None:
            return ranked_results

        return ranked_results[:limit]

    def _match_candidate(
        self,
        query: str,
        normalized_query: str,
        candidate: TrackCandidate,
    ) -> MatchResult:
        normalized_candidate = self._normalize(candidate.display_text)
        distance = self._distance(normalized_query, normalized_candidate)
        max_length = max(len(normalized_query), len(normalized_candidate))
        score = 1.0 if max_length == 0 else 1.0 - (distance / max_length)

        return MatchResult(
            track_id=candidate.track_id,
            query=query,
            candidate=candidate,
            score=round(score, 4),
            algorithm=self.algorithm_name,
            source=candidate.source,
            distance=distance,
            normalized_query=normalized_query,
            normalized_candidate=normalized_candidate,
            explanation=(
                "Score is normalized Levenshtein similarity: "
                f"1 - distance({distance}) / max_length({max_length})."
            ),
        )

    def _normalize(self, value: str) -> str:
        compacted_value = _WHITESPACE_RE.sub(" ", value.casefold().strip())
        return compacted_value

    def _distance(self, left: str, right: str) -> int:
        if left == right:
            return 0

        if not left:
            return len(right)

        if not right:
            return len(left)

        previous_row = list(range(len(right) + 1))
        for left_index, left_char in enumerate(left, start=1):
            current_row = [left_index]
            for right_index, right_char in enumerate(right, start=1):
                insertion_cost = current_row[right_index - 1] + 1
                deletion_cost = previous_row[right_index] + 1
                substitution_cost = previous_row[right_index - 1] + (
                    left_char != right_char
                )
                current_row.append(
                    min(insertion_cost, deletion_cost, substitution_cost)
                )
            previous_row = current_row

        return previous_row[-1]

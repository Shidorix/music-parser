"""Jaro-Winkler similarity matcher."""

from __future__ import annotations

from collections.abc import Sequence

from backend.core.matcher.base import BaseMatcher
from backend.core.matcher.normalization import normalize_match_text
from backend.core.matcher.schemas import MatchResult, TrackCandidate


class JaroWinklerMatcher(BaseMatcher):
    """Rank candidates by Jaro-Winkler similarity."""

    algorithm_name = "jaro_winkler"

    def __init__(
        self,
        *,
        prefix_scale: float = 0.1,
        max_prefix_length: int = 4,
    ) -> None:
        self._prefix_scale = prefix_scale
        self._max_prefix_length = max_prefix_length

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
        score = self._jaro_winkler_similarity(normalized_query, normalized_candidate)
        distance = round((1.0 - score) * 10000)

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
                "Score is Jaro-Winkler similarity. Distance is a scaled "
                "dissimilarity value: round((1 - score) * 10000)."
            ),
        )

    def _normalize(self, value: str) -> str:
        return normalize_match_text(value)

    def _jaro_winkler_similarity(self, left: str, right: str) -> float:
        jaro_similarity = self._jaro_similarity(left, right)
        prefix_length = self._common_prefix_length(left, right)

        return jaro_similarity + (
            prefix_length * self._prefix_scale * (1.0 - jaro_similarity)
        )

    def _jaro_similarity(self, left: str, right: str) -> float:
        if left == right:
            return 1.0

        left_length = len(left)
        right_length = len(right)
        if left_length == 0 or right_length == 0:
            return 0.0

        match_distance = max(max(left_length, right_length) // 2 - 1, 0)
        left_matches = [False] * left_length
        right_matches = [False] * right_length

        matches = 0
        for left_index, left_char in enumerate(left):
            start = max(0, left_index - match_distance)
            end = min(left_index + match_distance + 1, right_length)

            for right_index in range(start, end):
                if right_matches[right_index] or left_char != right[right_index]:
                    continue

                left_matches[left_index] = True
                right_matches[right_index] = True
                matches += 1
                break

        if matches == 0:
            return 0.0

        transpositions = 0
        right_index = 0
        for left_index, left_char in enumerate(left):
            if not left_matches[left_index]:
                continue

            while not right_matches[right_index]:
                right_index += 1

            if left_char != right[right_index]:
                transpositions += 1
            right_index += 1

        half_transpositions = transpositions / 2

        return (
            (matches / left_length)
            + (matches / right_length)
            + ((matches - half_transpositions) / matches)
        ) / 3

    def _common_prefix_length(self, left: str, right: str) -> int:
        max_length = min(len(left), len(right), self._max_prefix_length)

        for index in range(max_length):
            if left[index] != right[index]:
                return index

        return max_length

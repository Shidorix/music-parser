"""Weighted hybrid matcher that combines baseline string similarities."""

from __future__ import annotations

from collections.abc import Sequence

from backend.core.matcher.base import BaseMatcher
from backend.core.matcher.jaro_winkler import JaroWinklerMatcher
from backend.core.matcher.levenshtein import LevenshteinMatcher
from backend.core.matcher.schemas import MatchResult, TrackCandidate


class HybridMatcher(BaseMatcher):
    """Rank candidates with a weighted Levenshtein and Jaro-Winkler score."""

    algorithm_name = "hybrid_levenshtein_jaro_winkler"

    def __init__(
        self,
        *,
        levenshtein_weight: float = 0.35,
        jaro_winkler_weight: float = 0.65,
        levenshtein_matcher: LevenshteinMatcher | None = None,
        jaro_winkler_matcher: JaroWinklerMatcher | None = None,
    ) -> None:
        total_weight = levenshtein_weight + jaro_winkler_weight
        if total_weight <= 0:
            msg = "At least one hybrid matcher weight must be greater than zero."
            raise ValueError(msg)

        self._levenshtein_weight = levenshtein_weight / total_weight
        self._jaro_winkler_weight = jaro_winkler_weight / total_weight
        self._levenshtein_matcher = levenshtein_matcher or LevenshteinMatcher()
        self._jaro_winkler_matcher = jaro_winkler_matcher or JaroWinklerMatcher()

    def match(
        self,
        query: str,
        candidates: Sequence[TrackCandidate],
        *,
        limit: int | None = None,
    ) -> list[MatchResult]:
        """Match a query with a weighted score from two baseline matchers."""
        levenshtein_matches = self._levenshtein_matcher.match(query, candidates)
        jaro_winkler_matches = self._jaro_winkler_matcher.match(query, candidates)
        jaro_winkler_by_track_id = {
            match.track_id: match for match in jaro_winkler_matches
        }

        results: list[MatchResult] = []
        for levenshtein_match in levenshtein_matches:
            jaro_winkler_match = jaro_winkler_by_track_id[levenshtein_match.track_id]
            score = self._weighted_score(
                levenshtein_score=levenshtein_match.score,
                jaro_winkler_score=jaro_winkler_match.score,
            )
            distance = round((1.0 - score) * 10000)

            results.append(
                levenshtein_match.model_copy(
                    update={
                        "score": score,
                        "algorithm": self.algorithm_name,
                        "distance": distance,
                        "explanation": (
                            "Score is a weighted hybrid of normalized "
                            f"Levenshtein ({self._levenshtein_weight:.2f}) and "
                            f"Jaro-Winkler ({self._jaro_winkler_weight:.2f}) "
                            "similarities. Component scores: "
                            f"levenshtein={levenshtein_match.score:.4f}, "
                            f"jaro_winkler={jaro_winkler_match.score:.4f}."
                        ),
                    }
                )
            )

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

    def _weighted_score(
        self,
        *,
        levenshtein_score: float,
        jaro_winkler_score: float,
    ) -> float:
        return round(
            (levenshtein_score * self._levenshtein_weight)
            + (jaro_winkler_score * self._jaro_winkler_weight),
            4,
        )

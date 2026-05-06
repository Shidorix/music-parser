"""Playlist analytics service."""

from __future__ import annotations

from collections import Counter

from backend.core.analytics.schemas import PlaylistStatsResult
from backend.core.services import PersistedPlaylistResult


class PlaylistAnalyticsService:
    """Compute explainable quality metrics for persisted playlists."""

    def compute_stats(self, playlist: PersistedPlaylistResult) -> PlaylistStatsResult:
        """Compute aggregate parser and matcher metrics for a playlist."""
        match_scores = [
            item.match_score for item in playlist.items if item.match_score is not None
        ]
        parser_confidences = [item.parser_confidence for item in playlist.items]
        source_counts = Counter(
            item.source for item in playlist.items if item.source is not None
        )
        algorithm_counts = Counter(
            item.match_algorithm
            for item in playlist.items
            if item.match_algorithm is not None
        )
        uncertain_positions = tuple(
            item.position for item in playlist.items if item.is_uncertain
        )

        return PlaylistStatsResult(
            playlist_id=playlist.playlist_id,
            total_items=playlist.total_items,
            uncertain_count=len(uncertain_positions),
            confirmed_count=playlist.total_items - len(uncertain_positions),
            average_match_score=self._average(match_scores),
            average_parser_confidence=self._average(parser_confidences),
            source_counts=dict(source_counts),
            algorithm_counts=dict(algorithm_counts),
            uncertain_positions=uncertain_positions,
            explanation=(
                "Computed aggregate parser confidence, matcher score, source, "
                "algorithm, and manual-review metrics."
            ),
        )

    def _average(self, values: list[float]) -> float | None:
        if not values:
            return None
        return sum(values) / len(values)

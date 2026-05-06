"""Playlist analytics module."""

from backend.core.analytics.schemas import PlaylistStatsResult
from backend.core.analytics.service import PlaylistAnalyticsService

__all__ = [
    "PlaylistAnalyticsService",
    "PlaylistStatsResult",
]

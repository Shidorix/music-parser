"""Track search providers and aggregation service."""

from backend.core.search.providers import (
    DemoTrackSearchProvider,
    SpotifyTrackSearchProvider,
    TrackSearchProvider,
    YouTubeTrackSearchProvider,
)
from backend.core.search.schemas import (
    TrackSearchResult,
    TrackSearchSourceReport,
    TrackSearchSourceStatus,
)
from backend.core.search.service import TrackSearchService

__all__ = [
    "DemoTrackSearchProvider",
    "SpotifyTrackSearchProvider",
    "TrackSearchProvider",
    "TrackSearchResult",
    "TrackSearchService",
    "TrackSearchSourceReport",
    "TrackSearchSourceStatus",
    "YouTubeTrackSearchProvider",
]

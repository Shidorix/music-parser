"""External service integrations."""

from backend.integrations.spotify import SpotifyClient
from backend.integrations.youtube import YouTubeClient

__all__ = [
    "SpotifyClient",
    "YouTubeClient",
]

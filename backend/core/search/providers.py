"""Track search provider implementations."""

from __future__ import annotations

from typing import Protocol

from backend.core.catalog import InMemoryTrackCatalog
from backend.core.matcher import BaseMatcher, HybridMatcher, TrackCandidate
from backend.integrations import SpotifyClient, YouTubeClient


class TrackSearchProvider(Protocol):
    """Common interface for candidate search providers."""

    source_name: str

    async def search(self, query: str, *, limit: int) -> list[TrackCandidate]:
        """Search candidates for a query."""


class DemoTrackSearchProvider:
    """Search an in-memory demo catalog using the default fuzzy matcher."""

    source_name = "demo"

    def __init__(
        self,
        catalog: InMemoryTrackCatalog,
        matcher: BaseMatcher | None = None,
    ) -> None:
        self._catalog = catalog
        self._matcher = matcher or HybridMatcher()

    async def search(self, query: str, *, limit: int) -> list[TrackCandidate]:
        """Search demo candidates by fuzzy ranking."""
        candidates = self._catalog.list_candidates()
        matches = self._matcher.match(query=query, candidates=candidates, limit=limit)
        return [match.candidate for match in matches]


class SpotifyTrackSearchProvider:
    """Search candidates through the Spotify integration."""

    source_name = "spotify"

    def __init__(
        self,
        client: SpotifyClient,
        *,
        market: str | None = None,
    ) -> None:
        self._client = client
        self._market = market

    async def search(self, query: str, *, limit: int) -> list[TrackCandidate]:
        """Search Spotify candidates."""
        return await self._client.search_tracks(
            query=query,
            limit=limit,
            market=self._market,
        )


class YouTubeTrackSearchProvider:
    """Search candidates through the YouTube integration."""

    source_name = "youtube"

    def __init__(
        self,
        client: YouTubeClient,
        *,
        region_code: str | None = None,
        relevance_language: str | None = None,
    ) -> None:
        self._client = client
        self._region_code = region_code
        self._relevance_language = relevance_language

    async def search(self, query: str, *, limit: int) -> list[TrackCandidate]:
        """Search YouTube candidates."""
        return await self._client.search_videos(
            query=query,
            limit=limit,
            region_code=self._region_code,
            relevance_language=self._relevance_language,
        )

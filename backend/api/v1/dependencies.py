"""FastAPI dependencies for API v1."""

from __future__ import annotations

from backend.core.analytics import PlaylistAnalyticsService
from backend.core.catalog import InMemoryTrackCatalog
from backend.core.export import PlaylistExportService
from backend.core.matcher import TrackCandidate
from backend.core.search import (
    DemoTrackSearchProvider,
    SpotifyTrackSearchProvider,
    TrackSearchProvider,
    TrackSearchService,
    YouTubeTrackSearchProvider,
)
from backend.core.services import (
    ParseAndMatchService,
    ParseService,
    PlaylistPersistenceService,
    UserSessionService,
)
from backend.core.settings import Settings, get_settings
from backend.integrations import SpotifyClient, YouTubeClient


def get_parse_service() -> ParseService:
    """Create the parser-only service."""
    return ParseService()


def get_parse_and_match_service() -> ParseAndMatchService:
    """Create the parse-and-match service from application settings."""
    settings = get_settings()
    return ParseAndMatchService(
        confidence_threshold=settings.confidence_threshold,
        search_service=get_track_search_service(),
    )


def get_track_search_service() -> TrackSearchService:
    """Create the track search service from configured providers."""
    settings = get_settings()
    return TrackSearchService(build_track_search_providers(settings))


def get_playlist_persistence_service() -> PlaylistPersistenceService:
    """Create the playlist persistence service."""
    return PlaylistPersistenceService()


def get_playlist_export_service() -> PlaylistExportService:
    """Create the playlist export service."""
    return PlaylistExportService()


def get_playlist_analytics_service() -> PlaylistAnalyticsService:
    """Create the playlist analytics service."""
    return PlaylistAnalyticsService()


def get_user_session_service() -> UserSessionService:
    """Create the user session service."""
    return UserSessionService()


def build_track_search_providers(settings: Settings) -> list[TrackSearchProvider]:
    """Build search providers enabled by application settings."""
    providers: list[TrackSearchProvider] = []

    if settings.enable_demo_provider:
        providers.append(DemoTrackSearchProvider(get_demo_track_catalog()))

    if settings.spotify_access_token:
        providers.append(
            SpotifyTrackSearchProvider(
                SpotifyClient(access_token=settings.spotify_access_token),
                market=settings.spotify_market,
            )
        )

    if settings.youtube_api_key:
        providers.append(
            YouTubeTrackSearchProvider(
                YouTubeClient(api_key=settings.youtube_api_key),
                region_code=settings.youtube_region_code,
                relevance_language=settings.youtube_relevance_language,
            )
        )

    return providers


def get_demo_track_catalog() -> InMemoryTrackCatalog:
    """Return an in-memory catalog for the MVP API endpoint."""
    return InMemoryTrackCatalog(
        [
            TrackCandidate(
                track_id="demo:daft-punk-around-the-world",
                artist="Daft Punk",
                title="Around the World",
                source="demo",
            ),
            TrackCandidate(
                track_id="demo:kino-gruppa-krovi",
                artist="Kino",
                title="Gruppa Krovi",
                source="demo",
            ),
            TrackCandidate(
                track_id="demo:bonobo-kerala",
                artist="Bonobo",
                title="Kerala",
                source="demo",
            ),
            TrackCandidate(
                track_id="demo:radiohead-nude",
                artist="Radiohead",
                title="Nude",
                source="demo",
            ),
        ]
    )


def get_api_settings() -> Settings:
    """Return application settings for route dependencies."""
    return get_settings()

from backend.api.v1.dependencies import build_track_search_providers
from backend.core.search import (
    DemoTrackSearchProvider,
    SpotifyTrackSearchProvider,
    YouTubeTrackSearchProvider,
)
from backend.core.settings import Settings


def test_build_track_search_providers_uses_demo_by_default() -> None:
    providers = build_track_search_providers(Settings())

    assert len(providers) == 1
    assert isinstance(providers[0], DemoTrackSearchProvider)


def test_build_track_search_providers_enables_external_sources_from_settings() -> None:
    providers = build_track_search_providers(
        Settings(
            enable_demo_provider=False,
            spotify_access_token="spotify-token",
            spotify_market="US",
            youtube_api_key="youtube-key",
            youtube_region_code="US",
            youtube_relevance_language="en",
        )
    )

    assert len(providers) == 2
    assert isinstance(providers[0], SpotifyTrackSearchProvider)
    assert isinstance(providers[1], YouTubeTrackSearchProvider)

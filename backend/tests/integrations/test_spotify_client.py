import httpx
import pytest
import respx

from backend.core.exceptions import AppException
from backend.integrations import SpotifyClient


@pytest.mark.asyncio
async def test_search_tracks_maps_spotify_items_to_candidates() -> None:
    async with httpx.AsyncClient() as http_client:
        with respx.mock:
            route = respx.get("https://api.spotify.com/v1/search").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "tracks": {
                            "items": [
                                {
                                    "id": "track-1",
                                    "name": "Around the World",
                                    "artists": [{"name": "Daft Punk"}],
                                    "external_urls": {
                                        "spotify": "https://open.spotify.com/track/track-1",
                                    },
                                }
                            ]
                        }
                    },
                )
            )
            client = SpotifyClient(
                access_token="token",
                http_client=http_client,
            )

            results = await client.search_tracks("Daft Punk Around the World", limit=1)

    assert route.called
    assert results[0].track_id == "spotify:track-1"
    assert results[0].artist == "Daft Punk"
    assert results[0].title == "Around the World"
    assert results[0].source == "spotify"
    assert results[0].external_url == "https://open.spotify.com/track/track-1"


@pytest.mark.asyncio
async def test_search_tracks_can_use_client_credentials_token() -> None:
    async with httpx.AsyncClient() as http_client:
        with respx.mock:
            token_route = respx.post("https://accounts.spotify.com/api/token").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "client-token",
                        "token_type": "Bearer",
                        "expires_in": 3600,
                    },
                )
            )
            search_route = respx.get("https://api.spotify.com/v1/search").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "tracks": {
                            "items": [
                                {
                                    "id": "track-1",
                                    "name": "Around the World",
                                    "artists": [{"name": "Daft Punk"}],
                                }
                            ]
                        }
                    },
                )
            )
            client = SpotifyClient(
                client_id="client-id",
                client_secret="client-secret",
                http_client=http_client,
            )

            await client.search_tracks("Daft Punk Around the World", limit=1)
            await client.search_tracks("Daft Punk Around the World", limit=1)

    assert len(token_route.calls) == 1
    assert len(search_route.calls) == 2


@pytest.mark.asyncio
async def test_search_tracks_raises_app_exception_for_rate_limit() -> None:
    async with httpx.AsyncClient() as http_client:
        with respx.mock:
            respx.get("https://api.spotify.com/v1/search").mock(
                return_value=httpx.Response(429, json={"error": {"status": 429}})
            )
            client = SpotifyClient(
                access_token="token",
                http_client=http_client,
            )

            with pytest.raises(AppException) as exc_info:
                await client.search_tracks("Daft Punk", limit=1)

    assert exc_info.value.code == "SPOTIFY_RATE_LIMITED"
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_search_tracks_retries_transient_spotify_errors() -> None:
    async with httpx.AsyncClient() as http_client:
        with respx.mock:
            route = respx.get("https://api.spotify.com/v1/search").mock(
                side_effect=[
                    httpx.Response(500, json={"error": {"status": 500}}),
                    httpx.Response(
                        200,
                        json={
                            "tracks": {
                                "items": [
                                    {
                                        "id": "track-1",
                                        "name": "Around the World",
                                        "artists": [{"name": "Daft Punk"}],
                                    }
                                ]
                            }
                        },
                    ),
                ]
            )
            client = SpotifyClient(
                access_token="token",
                http_client=http_client,
                retry_backoff_seconds=0,
            )

            results = await client.search_tracks("Daft Punk", limit=1)

    assert len(route.calls) == 2
    assert results[0].track_id == "spotify:track-1"


@pytest.mark.asyncio
async def test_search_tracks_rejects_invalid_limit() -> None:
    client = SpotifyClient(access_token="token")

    with pytest.raises(AppException) as exc_info:
        await client.search_tracks("Daft Punk", limit=0)

    assert exc_info.value.code == "SPOTIFY_INVALID_LIMIT"


def test_spotify_client_requires_access_token() -> None:
    with pytest.raises(AppException) as exc_info:
        SpotifyClient(access_token="")

    assert exc_info.value.code == "SPOTIFY_CREDENTIALS_MISSING"

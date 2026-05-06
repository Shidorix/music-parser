import httpx
import pytest
import respx

from backend.core.exceptions import AppException
from backend.integrations import YouTubeClient


@pytest.mark.asyncio
async def test_search_videos_maps_youtube_items_to_candidates() -> None:
    async with httpx.AsyncClient() as http_client:
        with respx.mock:
            route = respx.get("https://www.googleapis.com/youtube/v3/search").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "items": [
                            {
                                "id": {
                                    "kind": "youtube#video",
                                    "videoId": "video-1",
                                },
                                "snippet": {
                                    "title": "Daft Punk - Around the World &amp; More",
                                    "channelTitle": "Daft Punk",
                                },
                            }
                        ]
                    },
                )
            )
            client = YouTubeClient(api_key="api-key", http_client=http_client)

            results = await client.search_videos(
                "Daft Punk Around the World",
                limit=1,
                region_code="US",
                relevance_language="en",
            )

    assert route.called
    assert results[0].track_id == "youtube:video-1"
    assert results[0].artist is None
    assert results[0].title == "Daft Punk - Around the World & More"
    assert results[0].source == "youtube"


@pytest.mark.asyncio
async def test_search_videos_skips_non_video_results() -> None:
    async with httpx.AsyncClient() as http_client:
        with respx.mock:
            respx.get("https://www.googleapis.com/youtube/v3/search").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "items": [
                            {
                                "id": {
                                    "kind": "youtube#channel",
                                    "channelId": "channel-1",
                                },
                                "snippet": {"title": "Some Channel"},
                            }
                        ]
                    },
                )
            )
            client = YouTubeClient(api_key="api-key", http_client=http_client)

            results = await client.search_videos("Daft Punk", limit=1)

    assert results == []


@pytest.mark.asyncio
async def test_search_videos_raises_app_exception_for_forbidden_response() -> None:
    async with httpx.AsyncClient() as http_client:
        with respx.mock:
            respx.get("https://www.googleapis.com/youtube/v3/search").mock(
                return_value=httpx.Response(403, json={"error": {"code": 403}})
            )
            client = YouTubeClient(api_key="api-key", http_client=http_client)

            with pytest.raises(AppException) as exc_info:
                await client.search_videos("Daft Punk", limit=1)

    assert exc_info.value.code == "YOUTUBE_FORBIDDEN"
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_search_videos_retries_transient_youtube_errors() -> None:
    async with httpx.AsyncClient() as http_client:
        with respx.mock:
            route = respx.get("https://www.googleapis.com/youtube/v3/search").mock(
                side_effect=[
                    httpx.Response(503, json={"error": {"code": 503}}),
                    httpx.Response(
                        200,
                        json={
                            "items": [
                                {
                                    "id": {
                                        "kind": "youtube#video",
                                        "videoId": "video-1",
                                    },
                                    "snippet": {
                                        "title": "Daft Punk - Around the World",
                                    },
                                }
                            ]
                        },
                    ),
                ]
            )
            client = YouTubeClient(
                api_key="api-key",
                http_client=http_client,
                retry_backoff_seconds=0,
            )

            results = await client.search_videos("Daft Punk", limit=1)

    assert len(route.calls) == 2
    assert results[0].track_id == "youtube:video-1"


@pytest.mark.asyncio
async def test_search_videos_rejects_invalid_limit() -> None:
    client = YouTubeClient(api_key="api-key")

    with pytest.raises(AppException) as exc_info:
        await client.search_videos("Daft Punk", limit=0)

    assert exc_info.value.code == "YOUTUBE_INVALID_LIMIT"


def test_youtube_client_requires_api_key() -> None:
    with pytest.raises(AppException) as exc_info:
        YouTubeClient(api_key="")

    assert exc_info.value.code == "YOUTUBE_API_KEY_MISSING"

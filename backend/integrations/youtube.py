"""Async YouTube Data API v3 integration."""

from __future__ import annotations

import asyncio
from html import unescape
from typing import Any, Final

import httpx

from backend.core.exceptions import AppException
from backend.core.matcher import TrackCandidate

YOUTUBE_API_BASE_URL: Final[str] = "https://www.googleapis.com/youtube/v3"


class YouTubeClient:
    """Small async client for YouTube video search."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = YOUTUBE_API_BASE_URL,
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.25,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key.strip():
            raise AppException(
                code="YOUTUBE_API_KEY_MISSING",
                message="YouTube API key is required.",
                status_code=500,
            )

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds
        self._http_client = http_client

    async def search_videos(
        self,
        query: str,
        *,
        limit: int = 10,
        region_code: str | None = None,
        relevance_language: str | None = None,
    ) -> list[TrackCandidate]:
        """Search YouTube videos and map them to catalog candidates."""
        if not query.strip():
            return []

        if not 1 <= limit <= 50:
            raise AppException(
                code="YOUTUBE_INVALID_LIMIT",
                message="YouTube search limit must be between 1 and 50.",
                status_code=400,
            )

        response_payload = await self._get_search_payload(
            query=query,
            limit=limit,
            region_code=region_code,
            relevance_language=relevance_language,
        )
        items = response_payload.get("items", [])

        if not isinstance(items, list):
            raise AppException(
                code="YOUTUBE_INVALID_RESPONSE",
                message="YouTube search response has an invalid items payload.",
                status_code=502,
            )

        return [
            self._map_search_item(item)
            for item in items
            if isinstance(item, dict) and self._is_video_result(item)
        ]

    async def _get_search_payload(
        self,
        query: str,
        limit: int,
        region_code: str | None,
        relevance_language: str | None,
    ) -> dict[str, Any]:
        request_params: dict[str, str | int] = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": limit,
            "key": self._api_key,
        }
        if region_code is not None:
            request_params["regionCode"] = region_code
        if relevance_language is not None:
            request_params["relevanceLanguage"] = relevance_language

        if self._http_client is not None:
            response = await self._request_with_retries(
                self._http_client,
                request_params,
            )
        else:
            async with httpx.AsyncClient() as http_client:
                response = await self._request_with_retries(
                    http_client,
                    request_params,
                )

        self._raise_for_youtube_status(response)
        payload = response.json()
        if not isinstance(payload, dict):
            raise AppException(
                code="YOUTUBE_INVALID_RESPONSE",
                message="YouTube search response is not a JSON object.",
                status_code=502,
            )

        return payload

    async def _request_with_retries(
        self,
        http_client: httpx.AsyncClient,
        request_params: dict[str, str | int],
    ) -> httpx.Response:
        attempts = self._max_retries + 1
        last_error: httpx.HTTPError | None = None

        for attempt in range(attempts):
            try:
                response = await http_client.get(
                    f"{self._base_url}/search",
                    params=request_params,
                    timeout=self._timeout_seconds,
                )
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < attempts - 1:
                    await self._sleep_before_retry(attempt)
                    continue
                break

            if (
                self._is_retryable_status(response.status_code)
                and attempt < attempts - 1
            ):
                await self._sleep_before_retry(attempt)
                continue

            return response

        raise AppException(
            code="YOUTUBE_REQUEST_FAILED",
            message="YouTube search request failed.",
            status_code=502,
        ) from last_error

    async def _sleep_before_retry(self, attempt: int) -> None:
        delay = self._retry_backoff_seconds * (2**attempt)
        if delay > 0:
            await asyncio.sleep(delay)

    def _is_retryable_status(self, status_code: int) -> bool:
        return status_code == 429 or status_code >= 500

    def _raise_for_youtube_status(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return

        error_code = {
            400: "YOUTUBE_BAD_REQUEST",
            401: "YOUTUBE_UNAUTHORIZED",
            403: "YOUTUBE_FORBIDDEN",
            429: "YOUTUBE_RATE_LIMITED",
        }.get(response.status_code, "YOUTUBE_REQUEST_FAILED")

        raise AppException(
            code=error_code,
            message=f"YouTube API returned HTTP {response.status_code}.",
            status_code=502,
        )

    def _is_video_result(self, item: dict[str, Any]) -> bool:
        item_id = item.get("id")
        return (
            isinstance(item_id, dict)
            and item_id.get("kind") == "youtube#video"
            and isinstance(item_id.get("videoId"), str)
        )

    def _map_search_item(self, item: dict[str, Any]) -> TrackCandidate:
        item_id = item.get("id")
        snippet = item.get("snippet")

        if not isinstance(item_id, dict) or not isinstance(snippet, dict):
            raise AppException(
                code="YOUTUBE_INVALID_RESPONSE",
                message="YouTube search item is missing id or snippet.",
                status_code=502,
            )

        video_id = item_id.get("videoId")
        title = snippet.get("title")

        if not isinstance(video_id, str) or not isinstance(title, str):
            raise AppException(
                code="YOUTUBE_INVALID_RESPONSE",
                message="YouTube video item is missing videoId or title.",
                status_code=502,
            )

        return TrackCandidate(
            track_id=f"youtube:{video_id}",
            artist=None,
            title=unescape(title),
            source="youtube",
        )

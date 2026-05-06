"""Async Spotify Web API integration."""

from __future__ import annotations

import asyncio
from typing import Any, Final

import httpx

from backend.core.exceptions import AppException
from backend.core.matcher import TrackCandidate

SPOTIFY_API_BASE_URL: Final[str] = "https://api.spotify.com/v1"


class SpotifyClient:
    """Small async client for Spotify track search."""

    def __init__(
        self,
        access_token: str,
        *,
        base_url: str = SPOTIFY_API_BASE_URL,
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.25,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not access_token.strip():
            raise AppException(
                code="SPOTIFY_TOKEN_MISSING",
                message="Spotify access token is required.",
                status_code=500,
            )

        self._access_token = access_token
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds
        self._http_client = http_client

    async def search_tracks(
        self,
        query: str,
        *,
        limit: int = 10,
        market: str | None = None,
    ) -> list[TrackCandidate]:
        """Search Spotify tracks and map them to catalog candidates."""
        if not query.strip():
            return []

        if not 1 <= limit <= 50:
            raise AppException(
                code="SPOTIFY_INVALID_LIMIT",
                message="Spotify search limit must be between 1 and 50.",
                status_code=400,
            )

        response_payload = await self._get_search_payload(
            query=query,
            limit=limit,
            market=market,
        )
        items = response_payload.get("tracks", {}).get("items", [])

        if not isinstance(items, list):
            raise AppException(
                code="SPOTIFY_INVALID_RESPONSE",
                message="Spotify search response has an invalid tracks payload.",
                status_code=502,
            )

        return [self._map_track_item(item) for item in items if isinstance(item, dict)]

    async def _get_search_payload(
        self,
        query: str,
        limit: int,
        market: str | None,
    ) -> dict[str, Any]:
        request_params: dict[str, str | int] = {
            "q": query,
            "type": "track",
            "limit": limit,
        }
        if market is not None:
            request_params["market"] = market

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

        self._raise_for_spotify_status(response)
        payload = response.json()
        if not isinstance(payload, dict):
            raise AppException(
                code="SPOTIFY_INVALID_RESPONSE",
                message="Spotify search response is not a JSON object.",
                status_code=502,
            )

        return payload

    def _build_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}"}

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
                    headers=self._build_headers(),
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
            code="SPOTIFY_REQUEST_FAILED",
            message="Spotify search request failed.",
            status_code=502,
        ) from last_error

    async def _sleep_before_retry(self, attempt: int) -> None:
        delay = self._retry_backoff_seconds * (2**attempt)
        if delay > 0:
            await asyncio.sleep(delay)

    def _is_retryable_status(self, status_code: int) -> bool:
        return status_code == 429 or status_code >= 500

    def _raise_for_spotify_status(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return

        error_code = {
            401: "SPOTIFY_UNAUTHORIZED",
            403: "SPOTIFY_FORBIDDEN",
            429: "SPOTIFY_RATE_LIMITED",
        }.get(response.status_code, "SPOTIFY_REQUEST_FAILED")

        raise AppException(
            code=error_code,
            message=f"Spotify API returned HTTP {response.status_code}.",
            status_code=502,
        )

    def _map_track_item(self, item: dict[str, Any]) -> TrackCandidate:
        track_id = item.get("id")
        title = item.get("name")
        artists = item.get("artists", [])

        if not isinstance(track_id, str) or not isinstance(title, str):
            raise AppException(
                code="SPOTIFY_INVALID_RESPONSE",
                message="Spotify track item is missing id or name.",
                status_code=502,
            )

        artist_names = [
            artist["name"]
            for artist in artists
            if isinstance(artist, dict) and isinstance(artist.get("name"), str)
        ]
        artist = ", ".join(artist_names) if artist_names else None

        return TrackCandidate(
            track_id=f"spotify:{track_id}",
            artist=artist,
            title=title,
            source="spotify",
        )

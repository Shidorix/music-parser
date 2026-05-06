"""Async Spotify Web API integration."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, Final

import httpx

from backend.core.exceptions import AppException
from backend.core.matcher import TrackCandidate

SPOTIFY_API_BASE_URL: Final[str] = "https://api.spotify.com/v1"
SPOTIFY_ACCOUNTS_BASE_URL: Final[str] = "https://accounts.spotify.com"


class SpotifyClient:
    """Small async client for Spotify track search."""

    def __init__(
        self,
        access_token: str | None = None,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        base_url: str = SPOTIFY_API_BASE_URL,
        accounts_base_url: str = SPOTIFY_ACCOUNTS_BASE_URL,
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.25,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        has_access_token = access_token is not None and bool(access_token.strip())
        has_client_credentials = (
            client_id is not None
            and bool(client_id.strip())
            and client_secret is not None
            and bool(client_secret.strip())
        )
        if not has_access_token and not has_client_credentials:
            raise AppException(
                code="SPOTIFY_CREDENTIALS_MISSING",
                message=("Spotify access token or client credentials are required."),
                status_code=500,
            )

        self._access_token = access_token.strip() if has_access_token else None
        self._client_id = client_id.strip() if client_id is not None else None
        self._client_secret = (
            client_secret.strip() if client_secret is not None else None
        )
        self._base_url = base_url.rstrip("/")
        self._accounts_base_url = accounts_base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds
        self._http_client = http_client
        self._cached_client_credentials_token: str | None = None
        self._cached_client_credentials_expires_at: datetime | None = None

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

    async def _build_headers(self, http_client: httpx.AsyncClient) -> dict[str, str]:
        access_token = self._access_token or await self._get_client_credentials_token(
            http_client
        )
        return {"Authorization": f"Bearer {access_token}"}

    async def _get_client_credentials_token(
        self,
        http_client: httpx.AsyncClient,
    ) -> str:
        if self._cached_client_credentials_token is not None:
            expires_at = self._cached_client_credentials_expires_at
            if expires_at is not None and expires_at > datetime.now(UTC):
                return self._cached_client_credentials_token

        if self._client_id is None or self._client_secret is None:
            raise AppException(
                code="SPOTIFY_CREDENTIALS_MISSING",
                message="Spotify client credentials are required.",
                status_code=500,
            )

        response = await http_client.post(
            f"{self._accounts_base_url}/api/token",
            data={"grant_type": "client_credentials"},
            auth=httpx.BasicAuth(self._client_id, self._client_secret),
            timeout=self._timeout_seconds,
        )
        self._raise_for_spotify_auth_status(response)

        payload = response.json()
        if not isinstance(payload, dict):
            raise AppException(
                code="SPOTIFY_INVALID_AUTH_RESPONSE",
                message="Spotify token response is not a JSON object.",
                status_code=502,
            )

        access_token = payload.get("access_token")
        expires_in = payload.get("expires_in", 3600)
        if not isinstance(access_token, str):
            raise AppException(
                code="SPOTIFY_INVALID_AUTH_RESPONSE",
                message="Spotify token response is missing access_token.",
                status_code=502,
            )
        if not isinstance(expires_in, int):
            expires_in = 3600

        self._cached_client_credentials_token = access_token
        self._cached_client_credentials_expires_at = datetime.now(UTC) + timedelta(
            seconds=max(expires_in - 60, 1)
        )
        return access_token

    async def _request_with_retries(
        self,
        http_client: httpx.AsyncClient,
        request_params: dict[str, str | int],
    ) -> httpx.Response:
        attempts = self._max_retries + 1
        last_error: httpx.HTTPError | None = None

        for attempt in range(attempts):
            try:
                headers = await self._build_headers(http_client)
                response = await http_client.get(
                    f"{self._base_url}/search",
                    headers=headers,
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

    def _raise_for_spotify_auth_status(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return

        error_code = {
            400: "SPOTIFY_AUTH_BAD_REQUEST",
            401: "SPOTIFY_AUTH_UNAUTHORIZED",
            403: "SPOTIFY_AUTH_FORBIDDEN",
            429: "SPOTIFY_RATE_LIMITED",
        }.get(response.status_code, "SPOTIFY_AUTH_FAILED")

        raise AppException(
            code=error_code,
            message=f"Spotify token endpoint returned HTTP {response.status_code}.",
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
        external_urls = item.get("external_urls")
        external_url = None
        if isinstance(external_urls, dict) and isinstance(
            external_urls.get("spotify"),
            str,
        ):
            external_url = external_urls["spotify"]

        return TrackCandidate(
            track_id=f"spotify:{track_id}",
            artist=artist,
            title=title,
            source="spotify",
            external_url=external_url,
        )

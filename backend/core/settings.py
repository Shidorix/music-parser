"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven backend settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PLAYLIST_PARSER_",
        extra="ignore",
    )

    environment: str = Field(
        default="development",
        description="Current application environment.",
    )
    database_url: str = Field(
        default="sqlite+aiosqlite:///./playlist_parser.db",
        description="SQLAlchemy async database URL.",
    )
    auto_create_tables: bool = Field(
        default=False,
        description=(
            "Whether the API should create database tables on startup. "
            "Useful only for quick MVP runs without Alembic migrations."
        ),
    )
    cors_allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated frontend origins allowed by CORS.",
    )
    confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Default threshold for uncertain match results.",
    )
    enable_demo_provider: bool = Field(
        default=True,
        description="Whether the in-memory demo search provider is enabled.",
    )
    spotify_access_token: str | None = Field(
        default=None,
        description="Spotify Web API access token.",
    )
    spotify_market: str | None = Field(
        default=None,
        description="Optional Spotify market code for search.",
    )
    youtube_api_key: str | None = Field(
        default=None,
        description="YouTube Data API v3 key.",
    )
    youtube_region_code: str | None = Field(
        default=None,
        description="Optional YouTube region code for search.",
    )
    youtube_relevance_language: str | None = Field(
        default=None,
        description="Optional YouTube relevance language for search.",
    )

    def parsed_cors_allowed_origins(self) -> list[str]:
        """Return configured CORS origins as a cleaned list."""
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()

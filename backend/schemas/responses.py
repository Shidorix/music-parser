"""Shared API response envelope schemas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

DataT = TypeVar("DataT")


class APIMeta(BaseModel):
    """Metadata included in successful API responses."""

    model_config = ConfigDict(frozen=True)

    total: int = Field(default=0, ge=0, description="Total number of returned items.")
    page: int = Field(default=0, ge=0, description="Current page index.")


class APIError(BaseModel):
    """Structured API error payload."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(description="Stable application error code.")
    message: str = Field(description="Human-readable error message.")


class APIResponse(BaseModel, Generic[DataT]):
    """Standard API response envelope."""

    model_config = ConfigDict(frozen=True)

    data: DataT | None = Field(default=None, description="Response payload.")
    meta: APIMeta | None = Field(default=None, description="Response metadata.")
    error: APIError | None = Field(default=None, description="Error payload.")

"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from backend.schemas import APIResponse

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Health status payload."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(description="Application health status.")
    version: str = Field(description="API version.")


@router.get(
    "",
    response_model=APIResponse[HealthResponse],
    summary="Check API health.",
    description="Returns a lightweight health status for backend availability checks.",
)
async def health_check() -> APIResponse[HealthResponse]:
    """Return the API health status."""
    return APIResponse(
        data=HealthResponse(status="ok", version="0.1.0"),
        meta=None,
        error=None,
    )

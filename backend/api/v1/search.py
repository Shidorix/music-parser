"""Track search API endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from backend.api.v1.dependencies import get_track_search_service
from backend.core.search import TrackSearchResult, TrackSearchService
from backend.schemas import APIMeta, APIResponse

router = APIRouter(prefix="/search", tags=["search"])


class TrackSearchRequest(BaseModel):
    """Request body for candidate search endpoint."""

    model_config = ConfigDict(frozen=True)

    query: str = Field(
        min_length=1,
        description="Track search query.",
        examples=["Daft Punk - Around the World"],
    )
    limit_per_source: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of candidates requested from each source.",
    )


@router.post(
    "",
    response_model=APIResponse[TrackSearchResult],
    summary="Search track candidates.",
    description=(
        "Searches configured candidate providers and returns deduplicated track "
        "candidates with per-source execution reports. The MVP endpoint uses the "
        "demo in-memory provider."
    ),
)
async def search_tracks(
    request: TrackSearchRequest,
    service: Annotated[TrackSearchService, Depends(get_track_search_service)],
) -> APIResponse[TrackSearchResult]:
    """Search track candidates across configured providers."""
    result = await service.search(
        query=request.query,
        limit_per_source=request.limit_per_source,
    )
    return APIResponse(
        data=result,
        meta=APIMeta(total=len(result.candidates), page=0),
        error=None,
    )

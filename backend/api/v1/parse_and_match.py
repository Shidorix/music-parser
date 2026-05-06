"""Parse-and-match API endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from backend.api.v1.dependencies import (
    get_parse_and_match_service,
)
from backend.core.services import ParseAndMatchResult, ParseAndMatchService
from backend.schemas import APIMeta, APIResponse

router = APIRouter(prefix="/parse-and-match", tags=["parse-and-match"])


class ParseAndMatchRequest(BaseModel):
    """Request body for parse-and-match endpoint."""

    model_config = ConfigDict(frozen=True)

    raw_lines: list[str] = Field(
        min_length=1,
        description="Raw track list lines to parse and match.",
        examples=[["Daft Punk - Around the World", "Кино - Группа крови"]],
    )
    match_limit: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum number of matches returned per input line.",
    )


@router.post(
    "",
    response_model=APIResponse[ParseAndMatchResult],
    summary="Parse raw track lines and match them against the demo catalog.",
    description=(
        "Runs the current NLP parser pipeline and default fuzzy matcher against "
        "an in-memory demo catalog. External Spotify/YouTube lookups can be "
        "enabled through configuration."
    ),
)
async def parse_and_match(
    request: ParseAndMatchRequest,
    service: Annotated[
        ParseAndMatchService,
        Depends(get_parse_and_match_service),
    ],
) -> APIResponse[ParseAndMatchResult]:
    """Parse raw lines and return ranked match candidates."""
    result = await service.parse_and_match(
        raw_lines=request.raw_lines,
        match_limit=request.match_limit,
    )
    return APIResponse(
        data=result,
        meta=APIMeta(total=result.total, page=0),
        error=None,
    )

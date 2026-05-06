"""Parser-only API endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from backend.api.v1.dependencies import get_parse_service
from backend.core.services import ParseLinesResult, ParseService
from backend.schemas import APIMeta, APIResponse

router = APIRouter(prefix="/parse", tags=["parse"])


class ParseRequest(BaseModel):
    """Request body for parser-only endpoint."""

    model_config = ConfigDict(frozen=True)

    raw_lines: list[str] = Field(
        min_length=1,
        description="Raw track list lines to parse.",
        examples=[["Daft Punk - Around the World", "Кино - Группа крови"]],
    )
    skip_blank: bool = Field(
        default=True,
        description="Whether blank lines should be omitted from parser results.",
    )


@router.post(
    "",
    response_model=APIResponse[ParseLinesResult],
    summary="Parse raw track lines without matching.",
    description=(
        "Runs the current parser pipeline and returns explainable parser metadata "
        "without matching against a catalog."
    ),
)
async def parse_lines(
    request: ParseRequest,
    service: Annotated[ParseService, Depends(get_parse_service)],
) -> APIResponse[ParseLinesResult]:
    """Parse raw track lines and return parser metadata."""
    result = service.parse_lines(
        raw_lines=request.raw_lines,
        skip_blank=request.skip_blank,
    )
    return APIResponse(
        data=result,
        meta=APIMeta(total=result.total, page=0),
        error=None,
    )

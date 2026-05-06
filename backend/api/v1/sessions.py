"""Anonymous user session API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.dependencies import get_user_session_service
from backend.core.services import UserSessionResult, UserSessionService
from backend.database import get_db_session
from backend.schemas import APIMeta, APIResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    """Request body for creating an anonymous user session."""

    model_config = ConfigDict(frozen=True)

    display_name: str | None = Field(
        default=None,
        max_length=255,
        description="Optional user-facing session label.",
    )


@router.post(
    "",
    response_model=APIResponse[UserSessionResult],
    summary="Create an anonymous user session.",
    description="Creates a session id that the frontend can persist locally.",
)
async def create_session(
    request: CreateSessionRequest,
    user_session_service: Annotated[
        UserSessionService,
        Depends(get_user_session_service),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> APIResponse[UserSessionResult]:
    """Create an anonymous user session."""
    user_session = await user_session_service.create_session(
        session,
        display_name=request.display_name,
    )
    await session.commit()
    return APIResponse(
        data=user_session,
        meta=APIMeta(total=1, page=0),
        error=None,
    )


@router.get(
    "/{session_id}",
    response_model=APIResponse[UserSessionResult],
    summary="Get an anonymous user session.",
    description="Loads one session by id.",
)
async def get_session(
    session_id: UUID,
    user_session_service: Annotated[
        UserSessionService,
        Depends(get_user_session_service),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> APIResponse[UserSessionResult]:
    """Load one anonymous user session."""
    user_session = await user_session_service.get_session(session, session_id)
    return APIResponse(
        data=user_session,
        meta=APIMeta(total=1, page=0),
        error=None,
    )


@router.post(
    "/{session_id}/touch",
    response_model=APIResponse[UserSessionResult],
    summary="Update session activity timestamp.",
    description="Refreshes the session last_seen_at timestamp.",
)
async def touch_session(
    session_id: UUID,
    user_session_service: Annotated[
        UserSessionService,
        Depends(get_user_session_service),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> APIResponse[UserSessionResult]:
    """Update session activity timestamp."""
    user_session = await user_session_service.touch_session(session, session_id)
    await session.commit()
    return APIResponse(
        data=user_session,
        meta=APIMeta(total=1, page=0),
        error=None,
    )

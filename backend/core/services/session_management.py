"""Service for anonymous user session lifecycle."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import AppException
from backend.core.services.schemas import UserSessionResult
from backend.crud import UserSessionCRUD, UserSessionCreate
from backend.models import UserSession


class UserSessionService:
    """Manage anonymous user sessions for playlist ownership."""

    def __init__(self, session_crud: UserSessionCRUD | None = None) -> None:
        self._session_crud = session_crud or UserSessionCRUD()

    async def create_session(
        self,
        session: AsyncSession,
        *,
        display_name: str | None,
    ) -> UserSessionResult:
        """Create a new anonymous user session."""
        user_session = await self._session_crud.create(
            session,
            UserSessionCreate(display_name=display_name),
        )
        return self._build_result(
            user_session,
            explanation="Created anonymous user session.",
        )

    async def get_session(
        self,
        session: AsyncSession,
        session_id: UUID,
    ) -> UserSessionResult:
        """Load one anonymous user session."""
        user_session = await self._session_crud.get_by_id(session, session_id)
        if user_session is None:
            raise AppException(
                code="SESSION_NOT_FOUND",
                message="User session was not found.",
                status_code=404,
            )
        return self._build_result(
            user_session,
            explanation="Loaded anonymous user session.",
        )

    async def touch_session(
        self,
        session: AsyncSession,
        session_id: UUID,
    ) -> UserSessionResult:
        """Update last seen timestamp for an anonymous user session."""
        user_session = await self._session_crud.touch(session, session_id)
        if user_session is None:
            raise AppException(
                code="SESSION_NOT_FOUND",
                message="User session was not found.",
                status_code=404,
            )
        return self._build_result(
            user_session,
            explanation="Updated anonymous user session activity timestamp.",
        )

    def _build_result(
        self,
        user_session: UserSession,
        *,
        explanation: str,
    ) -> UserSessionResult:
        return UserSessionResult(
            session_id=user_session.id,
            display_name=user_session.display_name,
            created_at=user_session.created_at,
            last_seen_at=user_session.last_seen_at,
            explanation=explanation,
        )

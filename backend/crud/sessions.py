"""CRUD operations for user sessions."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import UserSession
from backend.models.playlist import utc_now


class UserSessionCreate(BaseModel):
    """Input data for creating an anonymous user session."""

    model_config = ConfigDict(frozen=True)

    display_name: str | None = Field(default=None, max_length=255)


class UserSessionCRUD:
    """CRUD helper for anonymous user sessions."""

    async def create(
        self,
        session: AsyncSession,
        data: UserSessionCreate,
    ) -> UserSession:
        """Create a new user session."""
        user_session = UserSession(display_name=data.display_name)
        session.add(user_session)
        await session.flush()
        return user_session

    async def get_by_id(
        self,
        session: AsyncSession,
        session_id: UUID,
    ) -> UserSession | None:
        """Load one user session by id."""
        result = await session.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def touch(
        self,
        session: AsyncSession,
        session_id: UUID,
    ) -> UserSession | None:
        """Update last seen timestamp for a user session."""
        user_session = await self.get_by_id(session, session_id)
        if user_session is None:
            return None
        user_session.last_seen_at = utc_now()
        await session.flush()
        return user_session

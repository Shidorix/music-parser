"""Async SQLAlchemy engine and session helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.core.settings import get_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


def create_engine(database_url: str | None = None) -> AsyncEngine:
    """Create an async SQLAlchemy engine."""
    url = database_url or get_settings().database_url
    return create_async_engine(url, echo=False)


engine = create_engine()
SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_db(target_engine: AsyncEngine | None = None) -> None:
    """Create all registered database tables for the configured engine."""
    import backend.models  # noqa: F401

    database_engine = target_engine or engine
    async with database_engine.begin() as connection:
        typed_connection: AsyncConnection = connection
        await typed_connection.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Yield a database session for FastAPI dependencies."""
    async with SessionLocal() as session:
        yield session

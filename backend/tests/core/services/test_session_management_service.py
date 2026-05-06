from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.core.exceptions import AppException
from backend.core.services import UserSessionService
from backend.database import Base, create_engine


@pytest.mark.asyncio
async def test_creates_and_loads_user_session() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        service = UserSessionService()
        created = await service.create_session(
            session,
            display_name="Demo User",
        )
        await session.commit()

        loaded = await service.get_session(session, created.session_id)

    await engine.dispose()

    assert loaded.session_id == created.session_id
    assert loaded.display_name == "Demo User"


@pytest.mark.asyncio
async def test_get_session_raises_not_found() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        with pytest.raises(AppException) as error:
            await UserSessionService().get_session(session, uuid4())

    await engine.dispose()

    assert error.value.code == "SESSION_NOT_FOUND"

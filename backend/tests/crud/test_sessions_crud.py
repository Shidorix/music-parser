import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.crud import UserSessionCRUD, UserSessionCreate
from backend.database import Base, create_engine


@pytest.mark.asyncio
async def test_creates_loads_and_touches_user_session() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        crud = UserSessionCRUD()
        user_session = await crud.create(
            session,
            UserSessionCreate(display_name="Demo User"),
        )
        created_last_seen_at = user_session.last_seen_at
        await session.commit()

        loaded_session = await crud.get_by_id(session, user_session.id)
        touched_session = await crud.touch(session, user_session.id)

    await engine.dispose()

    assert loaded_session is not None
    assert loaded_session.id == user_session.id
    assert loaded_session.display_name == "Demo User"
    assert touched_session is not None
    assert touched_session.last_seen_at >= created_last_seen_at

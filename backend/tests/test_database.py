import pytest
from sqlalchemy import inspect

from backend.database import Base, create_engine, init_db


async def _table_names(connection) -> list[str]:
    return await connection.run_sync(
        lambda sync_connection: inspect(sync_connection).get_table_names()
    )


@pytest.mark.asyncio
async def test_init_db_creates_registered_tables() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")

    async with engine.connect() as connection:
        assert await _table_names(connection) == []

    try:
        await init_db(engine)

        async with engine.connect() as connection:
            table_names = await _table_names(connection)
    finally:
        await engine.dispose()

    assert sorted(table_names) == sorted(Base.metadata.tables)

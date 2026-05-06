from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.database import Base, create_engine, get_db_session
from backend.main import app


@pytest.mark.asyncio
async def test_creates_gets_and_touches_session() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_db_session() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            create_response = await client.post(
                "/api/v1/sessions",
                json={"display_name": "Demo User"},
            )
            session_id = create_response.json()["data"]["session_id"]

            get_response = await client.get(f"/api/v1/sessions/{session_id}")
            touch_response = await client.post(f"/api/v1/sessions/{session_id}/touch")
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    create_payload = create_response.json()
    get_payload = get_response.json()
    touch_payload = touch_response.json()

    assert create_response.status_code == 200
    assert create_payload["error"] is None
    assert create_payload["meta"] == {"total": 1, "page": 0}
    assert create_payload["data"]["display_name"] == "Demo User"

    assert get_response.status_code == 200
    assert get_payload["data"]["session_id"] == session_id

    assert touch_response.status_code == 200
    assert touch_payload["data"]["session_id"] == session_id


@pytest.mark.asyncio
async def test_get_session_returns_not_found_error() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_db_session() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/sessions/{uuid4()}")
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    payload = response.json()

    assert response.status_code == 404
    assert payload["data"] is None
    assert payload["error"]["code"] == "SESSION_NOT_FOUND"

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.database import Base, create_engine, get_db_session
from backend.main import app


@pytest.mark.asyncio
async def test_create_playlist_from_lines_persists_result() -> None:
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
            response = await client.post(
                "/api/v1/playlists",
                json={
                    "session_id": "session-1",
                    "name": "Demo Playlist",
                    "raw_lines": ["Daft Punk - Around the World"],
                    "match_limit": 1,
                },
            )
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    payload = response.json()

    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["meta"] == {"total": 1, "page": 0}
    assert payload["data"]["session_id"] == "session-1"
    assert payload["data"]["name"] == "Demo Playlist"
    assert payload["data"]["items"][0]["match_track_id"] == (
        "demo:daft-punk-around-the-world"
    )
    assert payload["data"]["items"][0]["parser_confidence"] > 0
    assert payload["data"]["items"][0]["match_algorithm"] == (
        "hybrid_levenshtein_jaro_winkler"
    )
    assert payload["data"]["items"][0]["source"] == "demo"


@pytest.mark.asyncio
async def test_reads_created_playlist_by_id_and_session() -> None:
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
                "/api/v1/playlists",
                json={
                    "session_id": "session-1",
                    "name": "Read Playlist",
                    "raw_lines": ["Radiohead - Nude"],
                    "match_limit": 1,
                },
            )
            playlist_id = create_response.json()["data"]["playlist_id"]

            get_response = await client.get(f"/api/v1/playlists/{playlist_id}")
            list_response = await client.get(
                "/api/v1/playlists",
                params={"session_id": "session-1"},
            )
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    get_payload = get_response.json()
    list_payload = list_response.json()

    assert get_response.status_code == 200
    assert get_payload["error"] is None
    assert get_payload["data"]["playlist_id"] == playlist_id
    assert get_payload["data"]["name"] == "Read Playlist"
    assert get_payload["data"]["items"][0]["match_track_id"] == "demo:radiohead-nude"

    assert list_response.status_code == 200
    assert list_payload["error"] is None
    assert list_payload["meta"] == {"total": 1, "page": 0}
    assert list_payload["data"][0]["playlist_id"] == playlist_id


@pytest.mark.asyncio
async def test_exports_created_playlist_as_csv() -> None:
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
                "/api/v1/playlists",
                json={
                    "session_id": "session-1",
                    "name": "Export Playlist",
                    "raw_lines": ["Daft Punk - Around the World"],
                    "match_limit": 1,
                },
            )
            playlist_id = create_response.json()["data"]["playlist_id"]

            response = await client.get(
                f"/api/v1/playlists/{playlist_id}/export",
                params={"format": "csv"},
            )
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    payload = response.json()

    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["meta"] == {"total": 1, "page": 0}
    assert payload["data"]["format"] == "csv"
    assert payload["data"]["filename"] == f"playlist-{playlist_id}.csv"
    assert "demo:daft-punk-around-the-world" in payload["data"]["content"]


@pytest.mark.asyncio
async def test_returns_created_playlist_stats() -> None:
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
                "/api/v1/playlists",
                json={
                    "session_id": "session-1",
                    "name": "Stats Playlist",
                    "raw_lines": [
                        "Daft Punk - Around the World",
                        "unmatched experimental draft",
                    ],
                    "match_limit": 1,
                },
            )
            playlist_id = create_response.json()["data"]["playlist_id"]

            response = await client.get(f"/api/v1/playlists/{playlist_id}/stats")
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    payload = response.json()

    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["meta"] == {"total": 2, "page": 0}
    assert payload["data"]["playlist_id"] == playlist_id
    assert payload["data"]["total_items"] == 2
    assert payload["data"]["source_counts"]["demo"] == 2
    assert "hybrid_levenshtein_jaro_winkler" in payload["data"]["algorithm_counts"]


@pytest.mark.asyncio
async def test_get_playlist_returns_not_found_error() -> None:
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
            response = await client.get(f"/api/v1/playlists/{uuid4()}")
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    payload = response.json()

    assert response.status_code == 404
    assert payload["data"] is None
    assert payload["error"]["code"] == "PLAYLIST_NOT_FOUND"


@pytest.mark.asyncio
async def test_reviews_playlist_item_and_persists_manual_match() -> None:
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
                "/api/v1/playlists",
                json={
                    "session_id": "session-1",
                    "name": "Review Playlist",
                    "raw_lines": ["Bonobo - Kerala"],
                    "match_limit": 1,
                },
            )
            playlist = create_response.json()["data"]
            playlist_id = playlist["playlist_id"]
            item_id = playlist["items"][0]["item_id"]

            review_response = await client.patch(
                f"/api/v1/playlists/{playlist_id}/items/{item_id}",
                json={
                    "match_track_id": "manual:bonobo-kerala-live",
                    "match_score": 0.97,
                    "match_algorithm": "manual",
                    "source": "manual",
                    "is_uncertain": False,
                },
            )
            get_response = await client.get(f"/api/v1/playlists/{playlist_id}")
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    review_payload = review_response.json()
    get_payload = get_response.json()

    assert review_response.status_code == 200
    assert review_payload["error"] is None
    assert review_payload["data"]["match_track_id"] == "manual:bonobo-kerala-live"
    assert review_payload["data"]["match_score"] == 0.97
    assert review_payload["data"]["match_algorithm"] == "manual"
    assert review_payload["data"]["source"] == "manual"
    assert review_payload["data"]["is_uncertain"] is False

    assert get_payload["data"]["items"][0]["match_track_id"] == (
        "manual:bonobo-kerala-live"
    )
    assert get_payload["data"]["uncertain_count"] == 0


@pytest.mark.asyncio
async def test_updates_playlist_name_and_deletes_item() -> None:
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
                "/api/v1/playlists",
                json={
                    "session_id": "session-1",
                    "name": "Before",
                    "raw_lines": [
                        "Daft Punk - Around the World",
                        "Radiohead - Nude",
                    ],
                    "match_limit": 1,
                },
            )
            playlist = create_response.json()["data"]
            playlist_id = playlist["playlist_id"]
            item_id = playlist["items"][0]["item_id"]

            update_response = await client.patch(
                f"/api/v1/playlists/{playlist_id}",
                json={"name": "After"},
            )
            delete_item_response = await client.delete(
                f"/api/v1/playlists/{playlist_id}/items/{item_id}"
            )
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    update_payload = update_response.json()
    delete_item_payload = delete_item_response.json()

    assert update_response.status_code == 200
    assert update_payload["data"]["name"] == "After"

    assert delete_item_response.status_code == 200
    assert delete_item_payload["data"]["total_items"] == 1
    assert delete_item_payload["data"]["items"][0]["raw_input"] == "Radiohead - Nude"


@pytest.mark.asyncio
async def test_deletes_playlist_and_returns_not_found_afterwards() -> None:
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
                "/api/v1/playlists",
                json={
                    "session_id": "session-1",
                    "name": "Delete Playlist",
                    "raw_lines": ["Bonobo - Kerala"],
                    "match_limit": 1,
                },
            )
            playlist_id = create_response.json()["data"]["playlist_id"]

            delete_response = await client.delete(f"/api/v1/playlists/{playlist_id}")
            get_response = await client.get(f"/api/v1/playlists/{playlist_id}")
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    delete_payload = delete_response.json()
    get_payload = get_response.json()

    assert delete_response.status_code == 200
    assert delete_payload["data"]["resource_id"] == playlist_id
    assert delete_payload["data"]["resource_type"] == "playlist"
    assert delete_payload["data"]["deleted"] is True

    assert get_response.status_code == 404
    assert get_payload["error"]["code"] == "PLAYLIST_NOT_FOUND"


@pytest.mark.asyncio
async def test_review_playlist_item_returns_not_found_error() -> None:
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
            response = await client.patch(
                f"/api/v1/playlists/{uuid4()}/items/{uuid4()}",
                json={
                    "match_track_id": "manual:missing",
                    "match_score": 0.9,
                },
            )
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    payload = response.json()

    assert response.status_code == 404
    assert payload["data"] is None
    assert payload["error"]["code"] == "PLAYLIST_ITEM_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_playlist_from_lines_validates_request_body() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/playlists",
            json={"session_id": "", "raw_lines": []},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

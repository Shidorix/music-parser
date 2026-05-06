import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.crud import PlaylistCRUD, PlaylistCreate, PlaylistItemCreate
from backend.database import Base, create_engine


@pytest.mark.asyncio
async def test_creates_and_loads_playlist_with_items() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        crud = PlaylistCRUD()
        playlist = await crud.create(
            session,
            PlaylistCreate(
                session_id="session-1",
                name="Test Playlist",
                items=(
                    PlaylistItemCreate(
                        position=0,
                        raw_input="Daft Punk - Around the World",
                        parsed_artist="daft punk",
                        parsed_title="around the world",
                        parser_confidence=0.9,
                        match_track_id="demo:daft-punk-around-the-world",
                        match_score=1.0,
                        match_algorithm="levenshtein",
                        source="demo",
                        is_uncertain=False,
                        metadata_json={"pattern": "artist_title"},
                    ),
                ),
            ),
        )
        await session.commit()

        loaded_playlist = await crud.get_by_id(session, playlist.id)

    await engine.dispose()

    assert loaded_playlist is not None
    assert loaded_playlist.id == playlist.id
    assert loaded_playlist.session_id == "session-1"
    assert len(loaded_playlist.items) == 1
    assert loaded_playlist.items[0].raw_input == "Daft Punk - Around the World"
    assert loaded_playlist.items[0].metadata_json == {"pattern": "artist_title"}


@pytest.mark.asyncio
async def test_lists_playlists_by_session() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        crud = PlaylistCRUD()
        await crud.create(session, PlaylistCreate(session_id="session-1"))
        await crud.create(session, PlaylistCreate(session_id="session-2"))
        await session.commit()

        playlists = await crud.list_by_session(session, "session-1")

    await engine.dispose()

    assert len(playlists) == 1
    assert playlists[0].session_id == "session-1"

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.core.catalog import InMemoryTrackCatalog
from backend.core.matcher import TrackCandidate
from backend.core.search import DemoTrackSearchProvider, TrackSearchService
from backend.core.services import ParseAndMatchService, PlaylistPersistenceService
from backend.crud import PlaylistCRUD
from backend.database import Base, create_engine


@pytest.mark.asyncio
async def test_persists_parse_and_match_result() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        parse_and_match_result = await ParseAndMatchService(
            confidence_threshold=0.8,
            search_service=TrackSearchService(
                [
                    DemoTrackSearchProvider(
                        InMemoryTrackCatalog(
                            [
                                TrackCandidate(
                                    track_id="demo:daft-punk-around-the-world",
                                    artist="Daft Punk",
                                    title="Around the World",
                                    source="demo",
                                    external_url="https://example.test/track",
                                )
                            ]
                        )
                    )
                ]
            ),
        ).parse_and_match(["Daft Punk - Around the World"], match_limit=1)

        persisted = await PlaylistPersistenceService().persist_parse_and_match_result(
            session,
            session_id="session-1",
            name="Demo Playlist",
            parse_and_match_result=parse_and_match_result,
        )
        await session.commit()

        loaded = await PlaylistCRUD().get_by_id(session, persisted.playlist_id)

    await engine.dispose()

    assert loaded is not None
    assert persisted.total_items == 1
    assert persisted.uncertain_count == 0
    assert persisted.items[0].match_track_id == "demo:daft-punk-around-the-world"
    assert persisted.items[0].match_external_url == "https://example.test/track"
    assert loaded.items[0].match_external_url == "https://example.test/track"
    assert loaded.items[0].metadata_json["parsed_track"]["pattern"] == "artist_title"

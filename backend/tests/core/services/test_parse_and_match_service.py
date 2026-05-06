import pytest

from backend.core.catalog import InMemoryTrackCatalog
from backend.core.matcher import TrackCandidate
from backend.core.search import DemoTrackSearchProvider, TrackSearchService
from backend.core.services import ParseAndMatchService

KINO_GRUPPA_KROVI_RU = (
    "\u043a\u0438\u043d\u043e - "
    "\u0433\u0440\u0443\u043f\u043f\u0430 "
    "\u043a\u0440\u043e\u0432\u0438"
)
TSOY_GRUPPA_KROVI_RU = (
    "\u0446\u043e\u0439 - "
    "\u0433\u0440\u0443\u043f\u043f\u0430 "
    "\u043a\u0440\u043e\u0432\u0438"
)
RADIOHEAD_NUDE_RU = (
    "\u0440\u0430\u0434\u0438\u043e\u0445\u0435\u0434 - \u043d\u044e\u0434"
)
NOISY_KINO_GRUPPA_KROVI_RU = (
    "\u043a\u0438\u043d\u043e\u0443 - "
    "\u0433\u0440\u0443\u043f "
    "\u043a\u0440\u043e\u0432\u0438\u0438"
)


@pytest.mark.asyncio
async def test_parse_and_match_service_matches_multiple_lines() -> None:
    catalog = InMemoryTrackCatalog(
        [
            TrackCandidate(
                track_id="spotify:daft",
                artist="Daft Punk",
                title="Around the World",
                source="spotify",
            ),
            TrackCandidate(
                track_id="spotify:kino",
                artist="Kino",
                title="Gruppa Krovi",
                source="spotify",
            ),
        ]
    )
    service = ParseAndMatchService(
        confidence_threshold=0.8,
        search_service=TrackSearchService([DemoTrackSearchProvider(catalog)]),
    )

    result = await service.parse_and_match(
        ["Daft Punk - Around the World", KINO_GRUPPA_KROVI_RU],
        match_limit=1,
    )

    assert result.total == 2
    assert result.uncertain_count == 0
    assert result.items[0].match_result.matches[0].track_id == "spotify:daft"
    assert result.items[1].match_result.matches[0].track_id == "spotify:kino"
    assert result.items[1].match_result.matches[0].query == "kino - gruppa krovi"
    assert result.items[0].source_reports[0].source == "demo"


@pytest.mark.asyncio
async def test_parse_and_match_service_uses_artist_alias_for_tsoy() -> None:
    catalog = InMemoryTrackCatalog(
        [
            TrackCandidate(
                track_id="spotify:kino",
                artist="Kino",
                title="Gruppa Krovi",
                source="spotify",
            ),
        ]
    )
    service = ParseAndMatchService(
        confidence_threshold=0.8,
        search_service=TrackSearchService([DemoTrackSearchProvider(catalog)]),
    )

    result = await service.parse_and_match([TSOY_GRUPPA_KROVI_RU], match_limit=1)

    assert result.total == 1
    assert result.uncertain_count == 0
    assert result.items[0].best_score == 1.0
    assert result.items[0].match_result.matches[0].query == "kino - gruppa krovi"


@pytest.mark.asyncio
async def test_parse_and_match_service_accepts_noisy_russian_transliteration() -> None:
    catalog = InMemoryTrackCatalog(
        [
            TrackCandidate(
                track_id="spotify:radiohead",
                artist="Radiohead",
                title="Nude",
                source="spotify",
            ),
            TrackCandidate(
                track_id="spotify:kino",
                artist="Kino",
                title="Gruppa Krovi",
                source="spotify",
            ),
        ]
    )
    service = ParseAndMatchService(
        confidence_threshold=0.8,
        search_service=TrackSearchService([DemoTrackSearchProvider(catalog)]),
    )

    result = await service.parse_and_match(
        [RADIOHEAD_NUDE_RU, NOISY_KINO_GRUPPA_KROVI_RU],
        match_limit=1,
    )

    assert result.uncertain_count == 0
    assert result.items[0].match_result.matches[0].track_id == "spotify:radiohead"
    assert result.items[0].best_score >= 0.8
    assert result.items[1].match_result.matches[0].track_id == "spotify:kino"
    assert result.items[1].best_score >= 0.8


@pytest.mark.asyncio
async def test_parse_and_match_service_marks_low_score_as_uncertain() -> None:
    catalog = InMemoryTrackCatalog(
        [
            TrackCandidate(
                track_id="spotify:other",
                artist="Boards of Canada",
                title="Roygbiv",
                source="spotify",
            )
        ]
    )
    service = ParseAndMatchService(
        confidence_threshold=0.8,
        search_service=TrackSearchService([DemoTrackSearchProvider(catalog)]),
    )

    result = await service.parse_and_match(["Daft Punk - Around the World"])

    assert result.total == 1
    assert result.uncertain_count == 1
    assert result.items[0].is_uncertain is True
    assert result.items[0].best_score < 0.8


@pytest.mark.asyncio
async def test_parse_and_match_service_skips_blank_lines() -> None:
    service = ParseAndMatchService(
        confidence_threshold=0.8,
        search_service=TrackSearchService([]),
    )

    result = await service.parse_and_match(["", "   "])

    assert result.total == 0
    assert result.items == ()


def test_parse_and_match_service_rejects_invalid_threshold() -> None:
    with pytest.raises(ValueError, match="confidence_threshold"):
        ParseAndMatchService(confidence_threshold=1.5)

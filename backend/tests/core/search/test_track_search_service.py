import pytest

from backend.core.catalog import InMemoryTrackCatalog
from backend.core.exceptions import AppException
from backend.core.matcher import TrackCandidate
from backend.core.search import (
    DemoTrackSearchProvider,
    TrackSearchService,
    TrackSearchSourceStatus,
)


class FailingProvider:
    source_name = "failing"

    async def search(self, query: str, *, limit: int) -> list[TrackCandidate]:
        raise AppException(
            code="PROVIDER_FAILED",
            message="Provider failed.",
            status_code=502,
        )


class StaticProvider:
    source_name = "static"

    def __init__(self, candidates: list[TrackCandidate]) -> None:
        self._candidates = candidates

    async def search(self, query: str, *, limit: int) -> list[TrackCandidate]:
        return self._candidates[:limit]


@pytest.mark.asyncio
async def test_demo_search_provider_returns_ranked_candidates() -> None:
    provider = DemoTrackSearchProvider(
        InMemoryTrackCatalog(
            [
                TrackCandidate(
                    track_id="demo:1",
                    artist="Daft Punk",
                    title="One More Time",
                    source="demo",
                ),
                TrackCandidate(
                    track_id="demo:2",
                    artist="Daft Punk",
                    title="Around the World",
                    source="demo",
                ),
            ]
        )
    )
    service = TrackSearchService([provider])

    result = await service.search("Daft Punk - Around the World", limit_per_source=1)

    assert result.candidates[0].track_id == "demo:2"
    assert result.source_reports[0].status == TrackSearchSourceStatus.SUCCESS
    assert result.source_reports[0].candidate_count == 1


@pytest.mark.asyncio
async def test_search_service_keeps_partial_results_when_provider_fails() -> None:
    service = TrackSearchService(
        [
            StaticProvider(
                [
                    TrackCandidate(
                        track_id="static:1",
                        artist="Radiohead",
                        title="Nude",
                        source="static",
                    )
                ]
            ),
            FailingProvider(),
        ]
    )

    result = await service.search("Radiohead - Nude")

    assert len(result.candidates) == 1
    assert result.source_reports[0].status == TrackSearchSourceStatus.SUCCESS
    assert result.source_reports[1].status == TrackSearchSourceStatus.FAILED
    assert result.source_reports[1].error_code == "PROVIDER_FAILED"


@pytest.mark.asyncio
async def test_search_service_can_raise_on_provider_failure() -> None:
    service = TrackSearchService([FailingProvider()], allow_partial=False)

    with pytest.raises(AppException) as exc_info:
        await service.search("Radiohead - Nude")

    assert exc_info.value.code == "PROVIDER_FAILED"


@pytest.mark.asyncio
async def test_search_service_deduplicates_by_source_and_track_id() -> None:
    duplicate = TrackCandidate(
        track_id="static:1",
        artist="Radiohead",
        title="Nude",
        source="static",
    )
    service = TrackSearchService(
        [
            StaticProvider([duplicate]),
            StaticProvider([duplicate]),
        ]
    )

    result = await service.search("Radiohead - Nude")

    assert result.candidates == (duplicate,)


@pytest.mark.asyncio
async def test_search_service_skips_empty_query() -> None:
    service = TrackSearchService([FailingProvider()])

    result = await service.search("   ")

    assert result.candidates == ()
    assert result.source_reports == ()

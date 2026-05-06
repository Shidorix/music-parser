"""Aggregate track search candidates from multiple providers."""

from __future__ import annotations

from collections.abc import Sequence

from backend.core.exceptions import AppException
from backend.core.matcher import TrackCandidate
from backend.core.search.providers import TrackSearchProvider
from backend.core.search.schemas import (
    TrackSearchResult,
    TrackSearchSourceReport,
    TrackSearchSourceStatus,
)


class TrackSearchService:
    """Search track candidates across configured providers."""

    def __init__(
        self,
        providers: Sequence[TrackSearchProvider],
        *,
        allow_partial: bool = True,
    ) -> None:
        self._providers = tuple(providers)
        self._allow_partial = allow_partial

    async def search(
        self,
        query: str,
        *,
        limit_per_source: int = 10,
    ) -> TrackSearchResult:
        """Search all providers and return deduplicated candidates."""
        if not query.strip():
            return TrackSearchResult(
                query=query,
                candidates=(),
                source_reports=(),
                explanation="Empty query produced no provider calls.",
            )

        candidates: list[TrackCandidate] = []
        reports: list[TrackSearchSourceReport] = []

        for provider in self._providers:
            try:
                provider_candidates = await provider.search(
                    query=query,
                    limit=limit_per_source,
                )
            except AppException as exc:
                if not self._allow_partial:
                    raise
                reports.append(
                    TrackSearchSourceReport(
                        source=provider.source_name,
                        status=TrackSearchSourceStatus.FAILED,
                        candidate_count=0,
                        error_code=exc.code,
                        error_message=exc.message,
                    )
                )
                continue

            candidates.extend(provider_candidates)
            reports.append(
                TrackSearchSourceReport(
                    source=provider.source_name,
                    status=TrackSearchSourceStatus.SUCCESS,
                    candidate_count=len(provider_candidates),
                )
            )

        return TrackSearchResult(
            query=query,
            candidates=tuple(self._deduplicate(candidates)),
            source_reports=tuple(reports),
            explanation="Searched configured providers and deduplicated candidates.",
        )

    def _deduplicate(
        self,
        candidates: Sequence[TrackCandidate],
    ) -> list[TrackCandidate]:
        deduplicated: dict[tuple[str, str], TrackCandidate] = {}

        for candidate in candidates:
            deduplicated.setdefault((candidate.source, candidate.track_id), candidate)

        return list(deduplicated.values())

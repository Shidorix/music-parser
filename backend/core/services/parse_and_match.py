"""End-to-end service for parsing input lines and matching candidates."""

from __future__ import annotations

from collections.abc import Sequence

from backend.core.matcher import MatchingService
from backend.core.parser import ParsedTrack, TrackParsingPipeline
from backend.core.search import TrackSearchService
from backend.core.services.schemas import ParseAndMatchItemResult, ParseAndMatchResult


class ParseAndMatchService:
    """Parse raw track lines and match each line against a candidate catalog."""

    def __init__(
        self,
        *,
        confidence_threshold: float,
        parser: TrackParsingPipeline | None = None,
        matching_service: MatchingService | None = None,
        search_service: TrackSearchService | None = None,
    ) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            msg = "confidence_threshold must be between 0.0 and 1.0."
            raise ValueError(msg)

        self._parser = parser or TrackParsingPipeline()
        self._matching_service = matching_service or MatchingService()
        self._search_service = search_service
        self._confidence_threshold = confidence_threshold

    async def parse_and_match(
        self,
        raw_lines: Sequence[str],
        *,
        match_limit: int = 3,
    ) -> ParseAndMatchResult:
        """Parse raw lines and return ranked matches for each parsed track."""
        item_results = []
        for raw_line in raw_lines:
            if not raw_line.strip():
                continue
            item_results.append(
                await self._parse_and_match_one(
                    raw_line=raw_line,
                    match_limit=match_limit,
                )
            )
        item_results_tuple = tuple(item_results)

        uncertain_count = sum(item.is_uncertain for item in item_results_tuple)

        return ParseAndMatchResult(
            items=item_results_tuple,
            total=len(item_results_tuple),
            uncertain_count=uncertain_count,
            confidence_threshold=self._confidence_threshold,
            explanation=(
                "Parsed each non-empty input line, searched candidate providers, "
                "and matched against the returned candidates."
            ),
        )

    async def _parse_and_match_one(
        self,
        raw_line: str,
        match_limit: int,
    ) -> ParseAndMatchItemResult:
        parsed_track = self._parser.parse_line(raw_line)
        search_query = self._build_search_query(parsed_track)
        if self._search_service is not None:
            search_result = await self._search_service.search(
                query=search_query,
                limit_per_source=match_limit,
            )
            candidates = search_result.candidates
            source_reports = search_result.source_reports
        else:
            candidates = ()
            source_reports = ()

        match_result = self._matching_service.match_parsed_track(
            parsed_track=parsed_track,
            candidates=candidates,
            limit=match_limit,
        )
        best_match = match_result.matches[0] if match_result.matches else None
        best_score = best_match.score if best_match is not None else 0.0
        is_uncertain = best_score < self._confidence_threshold

        return ParseAndMatchItemResult(
            parsed_track=parsed_track,
            match_result=match_result,
            source_reports=source_reports,
            best_score=best_score,
            is_uncertain=is_uncertain,
            explanation=self._build_item_explanation(
                best_score=best_score,
                is_uncertain=is_uncertain,
            ),
        )

    def _build_search_query(self, parsed_track: ParsedTrack) -> str:
        if parsed_track.artist and parsed_track.title:
            return f"{parsed_track.artist} - {parsed_track.title}"

        if parsed_track.title:
            return parsed_track.title

        return parsed_track.normalized_input

    def _build_item_explanation(self, best_score: float, is_uncertain: bool) -> str:
        if is_uncertain:
            return (
                f"Best match score {best_score:.4f} is below the configured "
                f"threshold {self._confidence_threshold:.4f}."
            )

        return (
            f"Best match score {best_score:.4f} meets the configured threshold "
            f"{self._confidence_threshold:.4f}."
        )

"""Service for parser-only workflows."""

from __future__ import annotations

from collections.abc import Sequence

from backend.core.parser import TrackParsingPipeline
from backend.core.services.schemas import ParseLinesResult


class ParseService:
    """Parse raw track lines without matching them against a catalog."""

    def __init__(self, parser: TrackParsingPipeline | None = None) -> None:
        self._parser = parser or TrackParsingPipeline()

    def parse_lines(
        self,
        raw_lines: Sequence[str],
        *,
        skip_blank: bool = True,
    ) -> ParseLinesResult:
        """Parse multiple raw lines and return parser metadata."""
        parsed_tracks = tuple(
            self._parser.parse_lines(raw_lines=raw_lines, skip_blank=skip_blank)
        )

        return ParseLinesResult(
            items=parsed_tracks,
            total=len(parsed_tracks),
            explanation=(
                "Ran normalization, language detection, transliteration metadata "
                "generation, and pattern detection for each input line."
            ),
        )

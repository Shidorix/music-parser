"""Public parser facade for track list input."""

from __future__ import annotations

from collections.abc import Sequence

from backend.core.parser.detector import PatternDetector
from backend.core.parser.schemas import ParsedTrack


class TrackParser:
    """Parse raw track list lines with the current parser strategy."""

    def __init__(self, pattern_detector: PatternDetector | None = None) -> None:
        self._pattern_detector = pattern_detector or PatternDetector()

    def parse_line(self, raw_input: str) -> ParsedTrack:
        """Parse one raw track line into a structured track candidate."""
        return self._pattern_detector.detect(raw_input)

    def parse_lines(
        self,
        raw_lines: Sequence[str],
        *,
        skip_blank: bool = True,
    ) -> list[ParsedTrack]:
        """Parse multiple raw track lines while preserving input order."""
        parsed_tracks: list[ParsedTrack] = []

        for raw_line in raw_lines:
            parsed_track = self.parse_line(raw_line)
            if skip_blank and parsed_track.normalized_input == "":
                continue
            parsed_tracks.append(parsed_track)

        return parsed_tracks

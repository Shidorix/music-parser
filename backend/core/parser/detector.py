"""Pattern detection for unstructured music track lines."""

from __future__ import annotations

import re
from typing import Final

from backend.core.parser.schemas import ParsedTrack, SeparatorParseOrder, TrackPattern

_INDEX_PREFIX_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?:\d{1,4}\s*[\).\]:-]\s*|[#*]\s+|[•-]\s+)"
)
_WHITESPACE_RE: Final[re.Pattern[str]] = re.compile(r"\s+")
_SEPARATOR_RE: Final[re.Pattern[str]] = re.compile(r"(?:\s+[-|]\s+|:\s+)")
_PARENTHESIS_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<title>.+?)\s*\((?P<artist>[^()]+)\)\s*$"
)
_BRACKETS_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<title>.+?)\s*\[(?P<artist>[^\[\]]+)\]\s*$"
)
_TRAILING_METADATA_RE: Final[re.Pattern[str]] = re.compile(
    r"\s*[\(\[]\s*"
    r"(?:official\s+(?:video|audio)|lyrics?|lyric\s+video|remaster(?:ed)?|"
    r"live|music\s+video|клип|текст)"
    r"\s*[\)\]]\s*$",
    re.IGNORECASE,
)
_METADATA_MARKERS: Final[tuple[str, ...]] = (
    "feat",
    "ft.",
    "ft ",
    "prod.",
    "official",
    "lyrics",
    "live",
)
_DASH_TRANSLATION: Final[dict[int, str]] = str.maketrans(
    {
        "—": "-",
        "–": "-",
        "−": "-",
    }
)


class PatternDetector:
    """Detect common artist/title patterns in a single track line."""

    def __init__(
        self,
        separator_parse_order: SeparatorParseOrder = SeparatorParseOrder.ARTIST_TITLE,
    ) -> None:
        self._separator_parse_order = separator_parse_order

    def detect(self, raw_input: str) -> ParsedTrack:
        """Parse one raw line into a structured track candidate."""
        normalized_input = self._normalize(raw_input)
        return self.detect_normalized(
            raw_input=raw_input, normalized_input=normalized_input
        )

    def detect_normalized(self, raw_input: str, normalized_input: str) -> ParsedTrack:
        """Parse one line using text that was normalized earlier in the pipeline."""
        if not normalized_input:
            return ParsedTrack(
                raw_input=raw_input,
                normalized_input="",
                artist=None,
                title=None,
                confidence=0.0,
                pattern=TrackPattern.UNKNOWN,
                explanation="Input line is empty after normalization.",
            )

        separator_result = self._detect_artist_title_separator(
            raw_input=raw_input,
            normalized_input=normalized_input,
        )
        if separator_result is not None:
            return separator_result

        parenthesis_result = self._detect_parenthesized_artist(
            raw_input=raw_input,
            normalized_input=normalized_input,
        )
        if parenthesis_result is not None:
            return parenthesis_result

        return ParsedTrack(
            raw_input=raw_input,
            normalized_input=normalized_input,
            artist=None,
            title=self._clean_title(normalized_input),
            confidence=0.25,
            pattern=TrackPattern.UNKNOWN,
            explanation=(
                "No supported artist-title pattern matched; line was kept as a "
                "possible title for later matching."
            ),
        )

    def _detect_artist_title_separator(
        self,
        raw_input: str,
        normalized_input: str,
    ) -> ParsedTrack | None:
        parts = _SEPARATOR_RE.split(normalized_input, maxsplit=1)
        if len(parts) != 2:
            return None

        left_part, right_part = (self._clean_field(part) for part in parts)
        if self._separator_parse_order == SeparatorParseOrder.TITLE_ARTIST:
            title = self._clean_title(left_part)
            artist = right_part
            pattern = TrackPattern.TITLE_ARTIST
            confidence = 0.78
            explanation = (
                "Detected a separator pattern using the configured title-artist "
                "parse order."
            )
        else:
            artist = left_part
            title = self._clean_title(right_part)
            pattern = TrackPattern.ARTIST_TITLE
            confidence = 0.9
            explanation = (
                "Detected a separator pattern using the configured artist-title "
                "parse order."
            )

        title = self._clean_title(title)
        if not artist or not title:
            return None

        return ParsedTrack(
            raw_input=raw_input,
            normalized_input=normalized_input,
            artist=artist,
            title=title,
            confidence=confidence,
            pattern=pattern,
            explanation=explanation,
        )

    def _detect_parenthesized_artist(
        self,
        raw_input: str,
        normalized_input: str,
    ) -> ParsedTrack | None:
        parenthesis_match = _PARENTHESIS_RE.match(normalized_input)
        if parenthesis_match is not None:
            pattern = TrackPattern.TITLE_ARTIST_PARENTHESIS
            title = self._clean_field(parenthesis_match.group("title"))
            artist = self._clean_field(parenthesis_match.group("artist"))
        else:
            brackets_match = _BRACKETS_RE.match(normalized_input)
            if brackets_match is None:
                return None
            pattern = TrackPattern.TITLE_ARTIST_BRACKETS
            title = self._clean_field(brackets_match.group("title"))
            artist = self._clean_field(brackets_match.group("artist"))

        if not title or not artist or self._looks_like_metadata(artist):
            return None

        return ParsedTrack(
            raw_input=raw_input,
            normalized_input=normalized_input,
            artist=artist,
            title=self._clean_title(title),
            confidence=0.82,
            pattern=pattern,
            explanation=(
                "Detected a title followed by a parenthesized or bracketed artist."
            ),
        )

    def _normalize(self, raw_input: str) -> str:
        line = raw_input.translate(_DASH_TRANSLATION).strip()
        line = _INDEX_PREFIX_RE.sub("", line)
        line = line.strip(" \t\"'")
        return _WHITESPACE_RE.sub(" ", line).strip()

    def _clean_field(self, value: str) -> str:
        return _WHITESPACE_RE.sub(" ", value.strip(" \t\"'")).strip()

    def _clean_title(self, value: str) -> str:
        without_metadata = _TRAILING_METADATA_RE.sub("", value)
        return self._clean_field(without_metadata)

    def _looks_like_metadata(self, value: str) -> bool:
        lowered_value = value.lower().strip()
        return any(lowered_value.startswith(marker) for marker in _METADATA_MARKERS)

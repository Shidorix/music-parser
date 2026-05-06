"""Composable parsing pipeline for raw track input."""

from __future__ import annotations

from collections.abc import Sequence

from backend.core.language import LanguageDetector
from backend.core.normalizer import TextNormalizer
from backend.core.parser.detector import PatternDetector
from backend.core.parser.schemas import ParsedTrack
from backend.core.transliterator import Transliterator


class TrackParsingPipeline:
    """Run the first parser pipeline stages in the required NLP order."""

    def __init__(
        self,
        text_normalizer: TextNormalizer | None = None,
        language_detector: LanguageDetector | None = None,
        transliterator: Transliterator | None = None,
        pattern_detector: PatternDetector | None = None,
    ) -> None:
        self._text_normalizer = text_normalizer or TextNormalizer()
        self._language_detector = language_detector or LanguageDetector()
        self._transliterator = transliterator or Transliterator()
        self._pattern_detector = pattern_detector or PatternDetector()

    def parse_line(self, raw_input: str) -> ParsedTrack:
        """Normalize and parse one raw track line."""
        normalized_text = self._text_normalizer.normalize(raw_input)
        language_detection = self._language_detector.detect(
            normalized_text.normalized_text
        )
        transliteration = self._transliterator.transliterate(
            text=normalized_text.normalized_text,
            language=language_detection.language,
        )
        parsed_track = self._pattern_detector.detect_normalized(
            raw_input=raw_input,
            normalized_input=normalized_text.normalized_text,
        )

        return parsed_track.model_copy(
            update={
                "language": language_detection.language,
                "language_confidence": language_detection.confidence,
                "language_explanation": language_detection.explanation,
                "normalization_steps": normalized_text.transformations,
                "transliteration_candidates": transliteration.candidates,
                "transliteration_explanation": transliteration.explanation,
            }
        )

    def parse_lines(
        self,
        raw_lines: Sequence[str],
        *,
        skip_blank: bool = True,
    ) -> list[ParsedTrack]:
        """Normalize and parse multiple raw track lines while preserving order."""
        parsed_tracks: list[ParsedTrack] = []

        for raw_line in raw_lines:
            parsed_track = self.parse_line(raw_line)
            if skip_blank and parsed_track.normalized_input == "":
                continue
            parsed_tracks.append(parsed_track)

        return parsed_tracks

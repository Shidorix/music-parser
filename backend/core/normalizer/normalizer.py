"""Text normalization for unstructured track input."""

from __future__ import annotations

import re
from typing import Final

from backend.core.normalizer.schemas import NormalizedText

_CONTROL_CHARS_RE: Final[re.Pattern[str]] = re.compile(r"[\x00-\x1f\x7f]")
_INDEX_PREFIX_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?:\d{1,4}\s*[\).\]:-]\s*|[#*]\s+|[\u2022-]\s+)"
)
_SPECIAL_CHARS_RE: Final[re.Pattern[str]] = re.compile(
    r"[^\w\s\-:|()\[\]&'.,+/]",
    re.UNICODE,
)
_WHITESPACE_RE: Final[re.Pattern[str]] = re.compile(r"\s+")
_DASH_TRANSLATION: Final[dict[int, str]] = str.maketrans(
    {
        "\u2014": "-",
        "\u2013": "-",
        "\u2212": "-",
    }
)


class TextNormalizer:
    """Normalize user-provided track text before parsing and matching."""

    def normalize(self, raw_text: str) -> NormalizedText:
        """Normalize one input line and record applied transformations."""
        transformations: list[str] = []
        normalized_text = raw_text

        stripped_text = normalized_text.strip()
        if stripped_text != normalized_text:
            transformations.append("trimmed_outer_whitespace")
        normalized_text = stripped_text

        without_control_chars = _CONTROL_CHARS_RE.sub(" ", normalized_text)
        if without_control_chars != normalized_text:
            transformations.append("removed_control_characters")
        normalized_text = without_control_chars

        with_normalized_dashes = normalized_text.translate(_DASH_TRANSLATION)
        if with_normalized_dashes != normalized_text:
            transformations.append("normalized_dash_characters")
        normalized_text = with_normalized_dashes

        without_index_prefix = _INDEX_PREFIX_RE.sub("", normalized_text)
        if without_index_prefix != normalized_text:
            transformations.append("removed_list_index_prefix")
        normalized_text = without_index_prefix

        lowercased_text = normalized_text.lower()
        if lowercased_text != normalized_text:
            transformations.append("lowercased_text")
        normalized_text = lowercased_text

        without_special_chars = _SPECIAL_CHARS_RE.sub(" ", normalized_text)
        if without_special_chars != normalized_text:
            transformations.append("removed_special_characters")
        normalized_text = without_special_chars

        compacted_text = _WHITESPACE_RE.sub(" ", normalized_text).strip()
        if compacted_text != normalized_text:
            transformations.append("collapsed_whitespace")
        normalized_text = compacted_text

        return NormalizedText(
            raw_text=raw_text,
            normalized_text=normalized_text,
            transformations=tuple(transformations),
        )

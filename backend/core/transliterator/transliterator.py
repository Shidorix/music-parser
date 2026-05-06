"""Rule-based Cyrillic and Latin transliteration."""

from __future__ import annotations

from typing import Final

from backend.core.language import DetectedLanguage
from backend.core.transliterator.schemas import (
    TransliterationCandidate,
    TransliterationDirection,
    TransliterationResult,
)

_CYRILLIC_TO_LATIN: Final[dict[str, str]] = {
    "\u0430": "a",
    "\u0431": "b",
    "\u0432": "v",
    "\u0433": "g",
    "\u0434": "d",
    "\u0435": "e",
    "\u0451": "yo",
    "\u0436": "zh",
    "\u0437": "z",
    "\u0438": "i",
    "\u0439": "y",
    "\u043a": "k",
    "\u043b": "l",
    "\u043c": "m",
    "\u043d": "n",
    "\u043e": "o",
    "\u043f": "p",
    "\u0440": "r",
    "\u0441": "s",
    "\u0442": "t",
    "\u0443": "u",
    "\u0444": "f",
    "\u0445": "kh",
    "\u0446": "ts",
    "\u0447": "ch",
    "\u0448": "sh",
    "\u0449": "shch",
    "\u044a": "",
    "\u044b": "y",
    "\u044c": "",
    "\u044d": "e",
    "\u044e": "yu",
    "\u044f": "ya",
}
_LATIN_MULTI_TO_CYRILLIC: Final[tuple[tuple[str, str], ...]] = (
    ("shch", "\u0449"),
    ("yo", "\u0451"),
    ("zh", "\u0436"),
    ("kh", "\u0445"),
    ("ts", "\u0446"),
    ("ch", "\u0447"),
    ("sh", "\u0448"),
    ("yu", "\u044e"),
    ("ya", "\u044f"),
)
_LATIN_TO_CYRILLIC: Final[dict[str, str]] = {
    "a": "\u0430",
    "b": "\u0431",
    "c": "\u043a",
    "d": "\u0434",
    "e": "\u0435",
    "f": "\u0444",
    "g": "\u0433",
    "h": "\u0445",
    "i": "\u0438",
    "j": "\u0434\u0436",
    "k": "\u043a",
    "l": "\u043b",
    "m": "\u043c",
    "n": "\u043d",
    "o": "\u043e",
    "p": "\u043f",
    "q": "\u043a",
    "r": "\u0440",
    "s": "\u0441",
    "t": "\u0442",
    "u": "\u0443",
    "v": "\u0432",
    "w": "\u0432",
    "x": "\u043a\u0441",
    "y": "\u0439",
    "z": "\u0437",
}


class Transliterator:
    """Generate transparent rule-based transliteration candidates."""

    def transliterate(
        self,
        text: str,
        language: DetectedLanguage,
    ) -> TransliterationResult:
        """Generate script variants according to the detected language."""
        candidates: list[TransliterationCandidate] = []

        if language in {DetectedLanguage.RU, DetectedLanguage.MIXED}:
            latin_text = self.to_latin(text)
            self._append_candidate(
                candidates=candidates,
                source_text=text,
                candidate_text=latin_text,
                direction=TransliterationDirection.CYRILLIC_TO_LATIN,
                confidence=0.9,
                explanation=(
                    "Cyrillic characters were converted to a Latin search variant."
                ),
            )

        if language in {DetectedLanguage.EN, DetectedLanguage.MIXED}:
            cyrillic_text = self.to_cyrillic(text)
            self._append_candidate(
                candidates=candidates,
                source_text=text,
                candidate_text=cyrillic_text,
                direction=TransliterationDirection.LATIN_TO_CYRILLIC,
                confidence=0.45,
                explanation=(
                    "Latin characters were converted to an approximate Cyrillic "
                    "search variant."
                ),
            )

        if not candidates:
            return TransliterationResult(
                source_text=text,
                candidates=(),
                explanation=(
                    "No transliteration candidates were generated for the detected "
                    "language."
                ),
            )

        return TransliterationResult(
            source_text=text,
            candidates=tuple(candidates),
            explanation="Generated rule-based transliteration candidates.",
        )

    def to_latin(self, text: str) -> str:
        """Convert Cyrillic characters to a Latin representation."""
        return "".join(_CYRILLIC_TO_LATIN.get(char, char) for char in text.lower())

    def to_cyrillic(self, text: str) -> str:
        """Convert Latin characters to an approximate Cyrillic representation."""
        lowered_text = text.lower()
        result: list[str] = []
        index = 0

        while index < len(lowered_text):
            matched = False
            for latin_chunk, cyrillic_chunk in _LATIN_MULTI_TO_CYRILLIC:
                if lowered_text.startswith(latin_chunk, index):
                    result.append(cyrillic_chunk)
                    index += len(latin_chunk)
                    matched = True
                    break

            if matched:
                continue

            char = lowered_text[index]
            result.append(_LATIN_TO_CYRILLIC.get(char, char))
            index += 1

        return "".join(result)

    def _append_candidate(
        self,
        candidates: list[TransliterationCandidate],
        source_text: str,
        candidate_text: str,
        direction: TransliterationDirection,
        confidence: float,
        explanation: str,
    ) -> None:
        if candidate_text == source_text:
            return

        if any(candidate.text == candidate_text for candidate in candidates):
            return

        candidates.append(
            TransliterationCandidate(
                text=candidate_text,
                direction=direction,
                confidence=confidence,
                explanation=explanation,
            )
        )

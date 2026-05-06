from backend.core.language import DetectedLanguage
from backend.core.transliterator import TransliterationDirection, Transliterator

KINO_GRUPPA_KROVI_RU = (
    "\u043a\u0438\u043d\u043e - "
    "\u0433\u0440\u0443\u043f\u043f\u0430 "
    "\u043a\u0440\u043e\u0432\u0438"
)


def test_converts_cyrillic_text_to_latin() -> None:
    transliterator = Transliterator()

    result = transliterator.transliterate(
        text=KINO_GRUPPA_KROVI_RU,
        language=DetectedLanguage.RU,
    )

    assert len(result.candidates) == 1
    assert result.candidates[0].text == "kino - gruppa krovi"
    assert result.candidates[0].direction == TransliterationDirection.CYRILLIC_TO_LATIN
    assert result.candidates[0].confidence == 0.9


def test_converts_latin_text_to_approximate_cyrillic() -> None:
    transliterator = Transliterator()

    result = transliterator.transliterate(
        text="kino - gruppa krovi",
        language=DetectedLanguage.EN,
    )

    assert len(result.candidates) == 1
    assert result.candidates[0].text == KINO_GRUPPA_KROVI_RU
    assert result.candidates[0].direction == TransliterationDirection.LATIN_TO_CYRILLIC
    assert result.candidates[0].confidence == 0.45


def test_generates_both_candidates_for_mixed_text() -> None:
    transliterator = Transliterator()

    result = transliterator.transliterate(
        text="\u043a\u0438\u043d\u043e - blood type",
        language=DetectedLanguage.MIXED,
    )

    directions = {candidate.direction for candidate in result.candidates}

    assert directions == {
        TransliterationDirection.CYRILLIC_TO_LATIN,
        TransliterationDirection.LATIN_TO_CYRILLIC,
    }


def test_skips_unknown_language() -> None:
    transliterator = Transliterator()

    result = transliterator.transliterate(
        text="123 - !!!",
        language=DetectedLanguage.UNKNOWN,
    )

    assert result.candidates == ()

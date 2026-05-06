import pytest

from backend.core.language import DetectedLanguage, LanguageDetector


def test_detects_russian_text() -> None:
    detector = LanguageDetector()

    result = detector.detect("кино - группа крови")

    assert result.language == DetectedLanguage.RU
    assert result.confidence == 1.0
    assert result.cyrillic_ratio == 1.0
    assert result.latin_ratio == 0.0


def test_detects_english_text() -> None:
    detector = LanguageDetector()

    result = detector.detect("daft punk - around the world")

    assert result.language == DetectedLanguage.EN
    assert result.confidence == 1.0
    assert result.cyrillic_ratio == 0.0
    assert result.latin_ratio == 1.0


def test_detects_mixed_text_when_both_scripts_are_significant() -> None:
    detector = LanguageDetector()

    result = detector.detect("кино - blood type")

    assert result.language == DetectedLanguage.MIXED
    assert result.confidence > 0.5
    assert result.cyrillic_ratio > 0.0
    assert result.latin_ratio > 0.0


def test_detects_unknown_when_no_supported_letters_exist() -> None:
    detector = LanguageDetector()

    result = detector.detect("123 - !!!")

    assert result.language == DetectedLanguage.UNKNOWN
    assert result.confidence == 0.0


def test_rejects_invalid_mixed_threshold() -> None:
    with pytest.raises(ValueError, match="mixed_threshold"):
        LanguageDetector(mixed_threshold=0.9)

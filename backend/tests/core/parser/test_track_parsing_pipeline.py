from backend.core.language import DetectedLanguage
from backend.core.parser import TrackParsingPipeline, TrackPattern
from backend.core.transliterator import TransliterationDirection


def test_pipeline_normalizes_before_pattern_detection() -> None:
    pipeline = TrackParsingPipeline()

    result = pipeline.parse_line("01. КИНО — Группа крови")

    assert result.artist == "кино"
    assert result.title == "группа крови"
    assert result.normalized_input == "кино - группа крови"
    assert result.language == DetectedLanguage.RU
    assert result.language_confidence == 1.0
    assert result.pattern == TrackPattern.ARTIST_TITLE
    assert result.normalization_steps == (
        "normalized_dash_characters",
        "removed_list_index_prefix",
        "lowercased_text",
    )
    assert len(result.transliteration_candidates) == 1
    assert result.transliteration_candidates[0].text == "kino - gruppa krovi"
    assert (
        result.transliteration_candidates[0].direction
        == TransliterationDirection.CYRILLIC_TO_LATIN
    )


def test_pipeline_skips_blank_lines_by_default() -> None:
    pipeline = TrackParsingPipeline()

    results = pipeline.parse_lines(["", "  Daft Punk - One More Time  "])

    assert len(results) == 1
    assert results[0].artist == "daft punk"
    assert results[0].title == "one more time"

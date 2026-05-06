from backend.core.parser import (
    PatternDetector,
    SeparatorParseOrder,
    TrackParser,
    TrackPattern,
)


def test_detects_artist_title_with_dash_separator() -> None:
    detector = PatternDetector()

    result = detector.detect("Daft Punk - Around the World")

    assert result.artist == "Daft Punk"
    assert result.title == "Around the World"
    assert result.pattern == TrackPattern.ARTIST_TITLE
    assert result.confidence == 0.9


def test_detects_title_artist_with_configured_separator_order() -> None:
    detector = PatternDetector(
        separator_parse_order=SeparatorParseOrder.TITLE_ARTIST,
    )

    result = detector.detect("Around the World - Daft Punk")

    assert result.artist == "Daft Punk"
    assert result.title == "Around the World"
    assert result.pattern == TrackPattern.TITLE_ARTIST
    assert result.confidence == 0.78


def test_detects_artist_title_after_number_prefix_and_em_dash() -> None:
    detector = PatternDetector()

    result = detector.detect("01. Кино — Группа крови")

    assert result.artist == "Кино"
    assert result.title == "Группа крови"
    assert result.pattern == TrackPattern.ARTIST_TITLE


def test_detects_title_artist_parenthesis_pattern() -> None:
    detector = PatternDetector()

    result = detector.detect("Around the World (Daft Punk)")

    assert result.artist == "Daft Punk"
    assert result.title == "Around the World"
    assert result.pattern == TrackPattern.TITLE_ARTIST_PARENTHESIS
    assert result.confidence == 0.82


def test_strips_common_trailing_video_metadata_from_title() -> None:
    detector = PatternDetector()

    result = detector.detect("Bonobo - Kerala (Official Video)")

    assert result.artist == "Bonobo"
    assert result.title == "Kerala"
    assert result.pattern == TrackPattern.ARTIST_TITLE


def test_returns_low_confidence_title_when_pattern_is_unknown() -> None:
    detector = PatternDetector()

    result = detector.detect("Unknown floating track name")

    assert result.artist is None
    assert result.title == "Unknown floating track name"
    assert result.pattern == TrackPattern.UNKNOWN
    assert result.confidence == 0.25


def test_track_parser_skips_blank_lines_by_default() -> None:
    parser = TrackParser()

    results = parser.parse_lines(["", "Radiohead - Nude", "   "])

    assert len(results) == 1
    assert results[0].artist == "Radiohead"
    assert results[0].title == "Nude"

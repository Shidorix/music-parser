from backend.core.matcher import MatchingService, TrackCandidate
from backend.core.parser import TrackParsingPipeline

KINO_GRUPPA_KROVI_RU = (
    "\u043a\u0438\u043d\u043e - "
    "\u0433\u0440\u0443\u043f\u043f\u0430 "
    "\u043a\u0440\u043e\u0432\u0438"
)
TSOY_GRUPPA_KROVI_RU = (
    "\u0446\u043e\u0439 - "
    "\u0433\u0440\u0443\u043f\u043f\u0430 "
    "\u043a\u0440\u043e\u0432\u0438"
)


def test_matches_parsed_track_using_parsed_fields() -> None:
    parsed_track = TrackParsingPipeline().parse_line("Daft Punk - Around the World")
    candidates = [
        TrackCandidate(
            track_id="spotify:1",
            artist="Daft Punk",
            title="One More Time",
            source="spotify",
        ),
        TrackCandidate(
            track_id="spotify:2",
            artist="Daft Punk",
            title="Around the World",
            source="spotify",
        ),
    ]

    result = MatchingService().match_parsed_track(parsed_track, candidates, limit=1)

    assert result.matches[0].track_id == "spotify:2"
    assert result.matches[0].score == 1.0
    assert result.matches[0].query_variant_source == "parsed_fields"


def test_matches_transliterated_query_variant() -> None:
    parsed_track = TrackParsingPipeline().parse_line(KINO_GRUPPA_KROVI_RU)
    candidates = [
        TrackCandidate(
            track_id="spotify:1",
            artist="Kino",
            title="Gruppa Krovi",
            source="spotify",
        )
    ]

    result = MatchingService().match_parsed_track(parsed_track, candidates, limit=1)

    assert result.matches[0].track_id == "spotify:1"
    assert result.matches[0].score == 1.0
    assert result.matches[0].query == "kino - gruppa krovi"
    assert result.matches[0].query_variant_source == (
        "transliteration:cyrillic_to_latin"
    )


def test_deduplicates_candidates_by_best_query_variant() -> None:
    parsed_track = TrackParsingPipeline().parse_line(KINO_GRUPPA_KROVI_RU)
    candidates = [
        TrackCandidate(
            track_id="spotify:1",
            artist="Kino",
            title="Gruppa Krovi",
            source="spotify",
        )
    ]

    result = MatchingService().match_parsed_track(parsed_track, candidates)

    assert len(result.matches) == 1
    assert result.matches[0].query_variant_source == (
        "transliteration:cyrillic_to_latin"
    )


def test_builds_title_only_query_for_unknown_artist() -> None:
    parsed_track = TrackParsingPipeline().parse_line("Unknown floating track name")

    variants = MatchingService().build_query_variants(parsed_track)

    assert variants[0].text == "unknown floating track name"
    assert variants[0].source == "parsed_title"


def test_expands_artist_alias_for_tsoy_to_kino() -> None:
    parsed_track = TrackParsingPipeline().parse_line(TSOY_GRUPPA_KROVI_RU)
    candidates = [
        TrackCandidate(
            track_id="spotify:1",
            artist="Kino",
            title="Gruppa Krovi",
            source="spotify",
        )
    ]

    result = MatchingService().match_parsed_track(parsed_track, candidates, limit=1)

    assert result.matches[0].track_id == "spotify:1"
    assert result.matches[0].score == 1.0
    assert result.matches[0].query == "kino - gruppa krovi"
    assert result.matches[0].query_variant_source == "artist_alias"

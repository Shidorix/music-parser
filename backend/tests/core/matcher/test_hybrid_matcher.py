import pytest

from backend.core.matcher import HybridMatcher, TrackCandidate


def test_hybrid_matcher_preserves_exact_match_score() -> None:
    matcher = HybridMatcher()
    candidates = [
        TrackCandidate(
            track_id="spotify:1",
            artist="Daft Punk",
            title="Around the World",
            source="spotify",
        )
    ]

    results = matcher.match("Daft Punk - Around the World", candidates)

    assert results[0].score == 1.0
    assert results[0].algorithm == "hybrid_levenshtein_jaro_winkler"


def test_hybrid_matcher_handles_transliterated_radiohead_query() -> None:
    matcher = HybridMatcher()
    candidates = [
        TrackCandidate(
            track_id="demo:radiohead-nude",
            artist="Radiohead",
            title="Nude",
            source="demo",
        )
    ]

    results = matcher.match("radiokhed - nyud", candidates)

    assert results[0].track_id == "demo:radiohead-nude"
    assert results[0].score >= 0.8


def test_hybrid_matcher_handles_noisy_kino_query() -> None:
    matcher = HybridMatcher()
    candidates = [
        TrackCandidate(
            track_id="demo:kino-gruppa-krovi",
            artist="Kino",
            title="Gruppa Krovi",
            source="demo",
        )
    ]

    results = matcher.match("kinou - grup krovii", candidates)

    assert results[0].track_id == "demo:kino-gruppa-krovi"
    assert results[0].score >= 0.8


def test_hybrid_matcher_ignores_common_youtube_title_noise() -> None:
    matcher = HybridMatcher()
    candidates = [
        TrackCandidate(
            track_id="youtube:video-1",
            artist=None,
            title="Daft Punk - Around the World (Official Music Video) [HD]",
            source="youtube",
            external_url="https://www.youtube.com/watch?v=video-1",
        )
    ]

    results = matcher.match("Daft Punk - Around the World", candidates)

    assert results[0].track_id == "youtube:video-1"
    assert results[0].score == 1.0
    assert results[0].normalized_candidate == "daft punk - around the world"


def test_hybrid_matcher_keeps_heavily_corrupted_query_below_threshold() -> None:
    matcher = HybridMatcher()
    candidates = [
        TrackCandidate(
            track_id="demo:bonobo-kerala",
            artist="Bonobo",
            title="Kerala",
            source="demo",
        )
    ]

    results = matcher.match("banabau - kerola", candidates)

    assert results[0].track_id == "demo:bonobo-kerala"
    assert results[0].score < 0.8


def test_hybrid_matcher_rejects_zero_total_weight() -> None:
    with pytest.raises(ValueError, match="weight"):
        HybridMatcher(levenshtein_weight=0.0, jaro_winkler_weight=0.0)

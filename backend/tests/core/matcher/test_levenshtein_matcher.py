from backend.core.matcher import LevenshteinMatcher, TrackCandidate


def test_ranks_exact_match_first() -> None:
    matcher = LevenshteinMatcher()
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

    results = matcher.match("Daft Punk - Around the World", candidates)

    assert results[0].track_id == "spotify:2"
    assert results[0].score == 1.0
    assert results[0].distance == 0
    assert results[0].algorithm == "levenshtein"


def test_handles_small_typo_with_high_score() -> None:
    matcher = LevenshteinMatcher()
    candidates = [
        TrackCandidate(
            track_id="spotify:1",
            artist="Radiohead",
            title="Nude",
            source="spotify",
        )
    ]

    results = matcher.match("Radiohed - Nude", candidates)

    assert results[0].distance == 1
    assert results[0].score > 0.9


def test_respects_limit() -> None:
    matcher = LevenshteinMatcher()
    candidates = [
        TrackCandidate(track_id="1", artist="A", title="Song A", source="test"),
        TrackCandidate(track_id="2", artist="B", title="Song B", source="test"),
    ]

    results = matcher.match("A - Song A", candidates, limit=1)

    assert len(results) == 1
    assert results[0].track_id == "1"


def test_matches_title_only_candidates() -> None:
    matcher = LevenshteinMatcher()
    candidates = [
        TrackCandidate(track_id="youtube:1", title="Unknown Track", source="youtube")
    ]

    results = matcher.match("unknown track", candidates)

    assert results[0].score == 1.0
    assert results[0].normalized_candidate == "unknown track"

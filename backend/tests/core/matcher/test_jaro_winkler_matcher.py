from backend.core.matcher import JaroWinklerMatcher, TrackCandidate


def test_jaro_winkler_ranks_exact_match_first() -> None:
    matcher = JaroWinklerMatcher()
    candidates = [
        TrackCandidate(
            track_id="demo:1",
            artist="Daft Punk",
            title="One More Time",
            source="demo",
        ),
        TrackCandidate(
            track_id="demo:2",
            artist="Daft Punk",
            title="Around the World",
            source="demo",
        ),
    ]

    results = matcher.match("Daft Punk - Around the World", candidates)

    assert results[0].track_id == "demo:2"
    assert results[0].score == 1.0
    assert results[0].algorithm == "jaro_winkler"


def test_jaro_winkler_handles_transposed_characters() -> None:
    matcher = JaroWinklerMatcher()
    candidates = [
        TrackCandidate(
            track_id="demo:1",
            artist="Radiohead",
            title="Nude",
            source="demo",
        )
    ]

    results = matcher.match("Raidohead - Nude", candidates)

    assert results[0].track_id == "demo:1"
    assert results[0].score > 0.95
    assert results[0].distance > 0


def test_jaro_winkler_respects_limit() -> None:
    matcher = JaroWinklerMatcher()
    candidates = [
        TrackCandidate(track_id="1", artist="A", title="Song A", source="test"),
        TrackCandidate(track_id="2", artist="B", title="Song B", source="test"),
    ]

    results = matcher.match("A - Song A", candidates, limit=1)

    assert len(results) == 1
    assert results[0].track_id == "1"

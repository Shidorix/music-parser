from datetime import UTC, datetime
from uuid import uuid4

from backend.core.analytics import PlaylistAnalyticsService
from backend.core.services import PersistedPlaylistItemResult, PersistedPlaylistResult


def test_computes_playlist_stats() -> None:
    playlist = PersistedPlaylistResult(
        playlist_id=uuid4(),
        session_id="session-1",
        name="Stats Playlist",
        created_at=datetime(2026, 5, 6, tzinfo=UTC),
        total_items=2,
        uncertain_count=1,
        items=(
            PersistedPlaylistItemResult(
                item_id=uuid4(),
                position=0,
                raw_input="Daft Punk - Around the World",
                parsed_artist="Daft Punk",
                parsed_title="Around the World",
                parser_confidence=0.9,
                match_track_id="demo:daft-punk-around-the-world",
                match_score=1.0,
                match_algorithm="levenshtein",
                source="demo",
                is_uncertain=False,
            ),
            PersistedPlaylistItemResult(
                item_id=uuid4(),
                position=1,
                raw_input="Unknown Track",
                parsed_artist=None,
                parsed_title="Unknown Track",
                parser_confidence=0.5,
                match_track_id=None,
                match_score=None,
                match_algorithm=None,
                source=None,
                is_uncertain=True,
            ),
        ),
        explanation="Loaded persisted playlist.",
    )

    stats = PlaylistAnalyticsService().compute_stats(playlist)

    assert stats.total_items == 2
    assert stats.uncertain_count == 1
    assert stats.confirmed_count == 1
    assert stats.average_match_score == 1.0
    assert stats.average_parser_confidence == 0.7
    assert stats.source_counts == {"demo": 1}
    assert stats.algorithm_counts == {"levenshtein": 1}
    assert stats.uncertain_positions == (1,)

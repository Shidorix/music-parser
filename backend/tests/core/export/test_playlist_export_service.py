from datetime import UTC, datetime
from uuid import uuid4

from backend.core.export import PlaylistExportFormat, PlaylistExportService
from backend.core.services import PersistedPlaylistItemResult, PersistedPlaylistResult


def test_exports_playlist_as_json() -> None:
    playlist = _build_playlist()

    result = PlaylistExportService().export_playlist(
        playlist,
        PlaylistExportFormat.JSON,
    )

    assert result.format == PlaylistExportFormat.JSON
    assert result.media_type == "application/json"
    assert '"session_id": "session-1"' in result.content
    assert '"match_track_id": "demo:daft-punk-around-the-world"' in result.content
    assert '"match_external_url": "https://example.test/track"' in result.content


def test_exports_playlist_as_csv() -> None:
    playlist = _build_playlist()

    result = PlaylistExportService().export_playlist(
        playlist,
        PlaylistExportFormat.CSV,
    )

    assert result.format == PlaylistExportFormat.CSV
    assert result.media_type == "text/csv"
    assert result.content.splitlines()[0] == (
        "position,raw_input,parsed_artist,parsed_title,parser_confidence,"
        "match_track_id,match_external_url,match_score,match_algorithm,source,"
        "is_uncertain"
    )
    assert "Daft Punk - Around the World" in result.content


def test_exports_playlist_as_m3u() -> None:
    playlist = _build_playlist()

    result = PlaylistExportService().export_playlist(
        playlist,
        PlaylistExportFormat.M3U,
    )

    assert result.format == PlaylistExportFormat.M3U
    assert result.media_type == "audio/x-mpegurl"
    assert result.content == (
        "#EXTM3U\n"
        "#EXTINF:-1,Daft Punk - Around the World\n"
        "https://example.test/track\n"
    )


def _build_playlist() -> PersistedPlaylistResult:
    return PersistedPlaylistResult(
        playlist_id=uuid4(),
        session_id="session-1",
        name="Demo Playlist",
        created_at=datetime(2026, 5, 6, tzinfo=UTC),
        total_items=1,
        uncertain_count=0,
        items=(
            PersistedPlaylistItemResult(
                item_id=uuid4(),
                position=0,
                raw_input="Daft Punk - Around the World",
                parsed_artist="Daft Punk",
                parsed_title="Around the World",
                parser_confidence=0.95,
                match_track_id="demo:daft-punk-around-the-world",
                match_external_url="https://example.test/track",
                match_score=1.0,
                match_algorithm="levenshtein",
                source="demo",
                is_uncertain=False,
            ),
        ),
        explanation="Loaded persisted playlist.",
    )

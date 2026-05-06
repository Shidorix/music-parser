"""Playlist export service."""

from __future__ import annotations

import csv
import io
import json
from uuid import UUID

from backend.core.export.schemas import PlaylistExportFormat, PlaylistExportResult
from backend.core.services import PersistedPlaylistItemResult, PersistedPlaylistResult


class PlaylistExportService:
    """Serialize persisted playlists into portable export formats."""

    def export_playlist(
        self,
        playlist: PersistedPlaylistResult,
        export_format: PlaylistExportFormat,
    ) -> PlaylistExportResult:
        """Serialize a playlist into the requested export format."""
        if export_format == PlaylistExportFormat.JSON:
            return self._export_json(playlist)
        if export_format == PlaylistExportFormat.CSV:
            return self._export_csv(playlist)
        return self._export_m3u(playlist)

    def _export_json(self, playlist: PersistedPlaylistResult) -> PlaylistExportResult:
        content = json.dumps(
            playlist.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
        return PlaylistExportResult(
            filename=self._build_filename(playlist.playlist_id, "json"),
            format=PlaylistExportFormat.JSON,
            media_type="application/json",
            content=content,
            total_items=playlist.total_items,
            explanation="Exported playlist as structured JSON.",
        )

    def _export_csv(self, playlist: PersistedPlaylistResult) -> PlaylistExportResult:
        output = io.StringIO()
        fieldnames = [
            "position",
            "raw_input",
            "parsed_artist",
            "parsed_title",
            "parser_confidence",
            "match_track_id",
            "match_external_url",
            "match_score",
            "match_algorithm",
            "source",
            "is_uncertain",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()

        for item in playlist.items:
            writer.writerow(self._build_csv_row(item))

        return PlaylistExportResult(
            filename=self._build_filename(playlist.playlist_id, "csv"),
            format=PlaylistExportFormat.CSV,
            media_type="text/csv",
            content=output.getvalue(),
            total_items=playlist.total_items,
            explanation="Exported playlist as CSV for spreadsheet analysis.",
        )

    def _export_m3u(self, playlist: PersistedPlaylistResult) -> PlaylistExportResult:
        lines = ["#EXTM3U"]
        for item in playlist.items:
            title = self._build_display_title(item)
            lines.append(f"#EXTINF:-1,{title}")
            lines.append(item.match_external_url or item.match_track_id or title)

        return PlaylistExportResult(
            filename=self._build_filename(playlist.playlist_id, "m3u"),
            format=PlaylistExportFormat.M3U,
            media_type="audio/x-mpegurl",
            content="\n".join(lines) + "\n",
            total_items=playlist.total_items,
            explanation="Exported playlist as M3U track references.",
        )

    def _build_csv_row(self, item: PersistedPlaylistItemResult) -> dict[str, object]:
        return {
            "position": item.position,
            "raw_input": item.raw_input,
            "parsed_artist": item.parsed_artist or "",
            "parsed_title": item.parsed_title or "",
            "parser_confidence": item.parser_confidence,
            "match_track_id": item.match_track_id or "",
            "match_external_url": item.match_external_url or "",
            "match_score": item.match_score if item.match_score is not None else "",
            "match_algorithm": item.match_algorithm or "",
            "source": item.source or "",
            "is_uncertain": item.is_uncertain,
        }

    def _build_display_title(self, item: PersistedPlaylistItemResult) -> str:
        if item.parsed_artist and item.parsed_title:
            return f"{item.parsed_artist} - {item.parsed_title}"
        if item.parsed_title:
            return item.parsed_title
        return item.raw_input

    def _build_filename(self, playlist_id: UUID, extension: str) -> str:
        return f"playlist-{playlist_id}.{extension}"

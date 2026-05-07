"""Audio download service."""

from __future__ import annotations

import asyncio
import io
import tempfile
import zipfile
from pathlib import Path

import yt_dlp

from backend.core.exceptions import AppException
from backend.core.services import PersistedPlaylistItemResult, PersistedPlaylistResult


class DownloadFailedError(AppException):
    """Exception raised when an audio download fails."""


class PlaylistDownloadService:
    """Service to download audio tracks from YouTube."""

    async def download_track(self, item: PersistedPlaylistItemResult) -> tuple[bytes, str]:
        """Download a single track and return its mp3 bytes and filename."""
        if not self._is_youtube_url(item.match_external_url):
            raise DownloadFailedError("Track does not have a valid YouTube URL.")

        url = item.match_external_url
        filename_base = self._build_display_title(item)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            ydl_opts = {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "outtmpl": str(temp_path / f"{filename_base}.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
            }
            
            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            
            try:
                await asyncio.to_thread(_download)
            except Exception as e:
                raise DownloadFailedError(f"Failed to download {filename_base}: {e}") from e
            
            # Find the downloaded file
            downloaded_files = list(temp_path.glob("*.mp3"))
            if not downloaded_files:
                raise DownloadFailedError(f"No mp3 file generated for {filename_base}")
                
            mp3_file = downloaded_files[0]
            with open(mp3_file, "rb") as f:
                content = f.read()
                
            return content, f"{filename_base}.mp3"

    async def download_playlist_zip(self, playlist: PersistedPlaylistResult) -> bytes:
        """Download all valid tracks in a playlist and return a ZIP file containing them."""
        # Filter for items that have a youtube url
        items_to_download = [
            item for item in playlist.items 
            if self._is_youtube_url(item.match_external_url)
        ]
        
        if not items_to_download:
            raise DownloadFailedError("No playable YouTube URLs found in the playlist.")
            
        zip_buffer = io.BytesIO()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Using concurrent tasks for yt-dlp might cause rate limits, but sequential is slow.
            # We will do sequential to be safe for MVP and avoid banning.
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for idx, item in enumerate(items_to_download, start=1):
                    url = item.match_external_url
                    # Prepend index to keep playlist order
                    filename_base = f"{idx:02d} - {self._build_display_title(item)}"
                    
                    ydl_opts = {
                        "format": "bestaudio/best",
                        "postprocessors": [
                            {
                                "key": "FFmpegExtractAudio",
                                "preferredcodec": "mp3",
                                "preferredquality": "192",
                            }
                        ],
                        "outtmpl": str(temp_path / f"{filename_base}.%(ext)s"),
                        "quiet": True,
                        "no_warnings": True,
                    }
                    
                    def _download():
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([url])
                    
                    try:
                        await asyncio.to_thread(_download)
                    except Exception:
                        # Skip failed downloads for playlist zip
                        continue
                    
                    # Find and add the downloaded file to the zip
                    downloaded_files = list(temp_path.glob(f"{filename_base}*.mp3"))
                    if downloaded_files:
                        mp3_file = downloaded_files[0]
                        zf.write(mp3_file, arcname=mp3_file.name)
                        
        zip_buffer.seek(0)
        return zip_buffer.read()

    def _is_youtube_url(self, url: str | None) -> bool:
        if not url:
            return False
        return "youtube.com" in url or "youtu.be" in url

    def _build_display_title(self, item: PersistedPlaylistItemResult) -> str:
        # Avoid illegal path characters
        def sanitize(text: str) -> str:
            return "".join(c for c in text if c.isalnum() or c in " -_()").strip()

        if item.parsed_artist and item.parsed_title:
            return f"{sanitize(item.parsed_artist)} - {sanitize(item.parsed_title)}"
        if item.parsed_title:
            return sanitize(item.parsed_title)
        return sanitize(item.raw_input)

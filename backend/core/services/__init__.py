"""Application core services that compose parser and matcher modules."""

from backend.core.services.parse import ParseService
from backend.core.services.parse_and_match import ParseAndMatchService
from backend.core.services.playlist_persistence import PlaylistPersistenceService
from backend.core.services.schemas import (
    DeletedResourceResult,
    ParseAndMatchItemResult,
    ParseAndMatchResult,
    ParseLinesResult,
    PersistedPlaylistItemResult,
    PersistedPlaylistResult,
    UserSessionResult,
)
from backend.core.services.session_management import UserSessionService

__all__ = [
    "DeletedResourceResult",
    "ParseAndMatchItemResult",
    "ParseAndMatchResult",
    "ParseAndMatchService",
    "ParseLinesResult",
    "ParseService",
    "PersistedPlaylistItemResult",
    "PersistedPlaylistResult",
    "PlaylistPersistenceService",
    "UserSessionResult",
    "UserSessionService",
]

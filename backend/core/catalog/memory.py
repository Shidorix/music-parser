"""In-memory track catalog for tests and local demos."""

from __future__ import annotations

from collections.abc import Sequence

from backend.core.matcher import TrackCandidate


class InMemoryTrackCatalog:
    """Simple catalog implementation backed by an in-memory candidate list."""

    def __init__(self, candidates: Sequence[TrackCandidate]) -> None:
        self._candidates = tuple(candidates)

    def list_candidates(self) -> tuple[TrackCandidate, ...]:
        """Return all available candidates."""
        return self._candidates

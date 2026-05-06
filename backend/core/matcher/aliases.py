"""Domain-specific artist alias expansion for matching."""

from __future__ import annotations

from typing import Final

from backend.core.transliterator import Transliterator

_ARTIST_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "\u0446\u043e\u0439": ("\u043a\u0438\u043d\u043e", "kino"),
    "\u0432\u0438\u043a\u0442\u043e\u0440 \u0446\u043e\u0439": (
        "\u043a\u0438\u043d\u043e",
        "kino",
    ),
    "tsoy": ("kino", "\u043a\u0438\u043d\u043e"),
    "tsoi": ("kino", "\u043a\u0438\u043d\u043e"),
    "viktor tsoy": ("kino", "\u043a\u0438\u043d\u043e"),
    "viktor tsoi": ("kino", "\u043a\u0438\u043d\u043e"),
}


class ArtistAliasExpander:
    """Expand known artist aliases into canonical search variants."""

    def __init__(self, transliterator: Transliterator | None = None) -> None:
        self._transliterator = transliterator or Transliterator()

    def expand(self, artist: str | None, title: str | None) -> tuple[str, ...]:
        """Build artist-title variants for known aliases."""
        if artist is None or title is None:
            return ()

        aliases = _ARTIST_ALIASES.get(self._normalize(artist))
        if aliases is None:
            return ()

        variants: list[str] = []
        for canonical_artist in aliases:
            self._append_variant(variants, f"{canonical_artist} - {title}")

        for variant in tuple(variants):
            self._append_variant(variants, self._transliterator.to_latin(variant))

        return tuple(variants)

    def _normalize(self, value: str) -> str:
        return " ".join(value.casefold().strip().split())

    def _append_variant(self, variants: list[str], value: str) -> None:
        compacted_value = " ".join(value.strip().split())
        if not compacted_value:
            return

        if any(
            existing.casefold() == compacted_value.casefold() for existing in variants
        ):
            return

        variants.append(compacted_value)

"""Service layer that connects parsed tracks to matching algorithms."""

from __future__ import annotations

from collections.abc import Sequence

from backend.core.matcher.aliases import ArtistAliasExpander
from backend.core.matcher.base import BaseMatcher
from backend.core.matcher.hybrid import HybridMatcher
from backend.core.matcher.schemas import (
    MatchQueryVariant,
    MatchResult,
    ParsedTrackMatchResult,
    TrackCandidate,
)
from backend.core.parser import ParsedTrack


class MatchingService:
    """Build query variants from parsed tracks and rank candidate matches."""

    def __init__(
        self,
        matcher: BaseMatcher | None = None,
        alias_expander: ArtistAliasExpander | None = None,
    ) -> None:
        self._matcher = matcher or HybridMatcher()
        self._alias_expander = alias_expander or ArtistAliasExpander()

    def match_parsed_track(
        self,
        parsed_track: ParsedTrack,
        candidates: Sequence[TrackCandidate],
        *,
        limit: int | None = None,
    ) -> ParsedTrackMatchResult:
        """Match one parsed track against candidate records."""
        query_variants = self.build_query_variants(parsed_track)
        all_matches: list[MatchResult] = []

        for query_variant in query_variants:
            variant_matches = self._matcher.match(
                query=query_variant.text,
                candidates=candidates,
            )
            all_matches.extend(
                match.model_copy(
                    update={
                        "query_variant_source": query_variant.source,
                        "query_variant_confidence": query_variant.confidence,
                    }
                )
                for match in variant_matches
            )

        ranked_matches = self._rank_and_deduplicate(all_matches)
        if limit is not None:
            ranked_matches = ranked_matches[:limit]

        return ParsedTrackMatchResult(
            parsed_track_raw_input=parsed_track.raw_input,
            query_variants=tuple(query_variants),
            matches=tuple(ranked_matches),
            explanation=(
                "Generated query variants from parsed fields and transliteration "
                "metadata, then kept the best match per candidate."
            ),
        )

    def build_query_variants(
        self, parsed_track: ParsedTrack
    ) -> tuple[MatchQueryVariant, ...]:
        """Build deduplicated query variants from parser output."""
        variants: list[MatchQueryVariant] = []

        if parsed_track.artist and parsed_track.title:
            self._append_variant(
                variants=variants,
                text=f"{parsed_track.artist} - {parsed_track.title}",
                source="parsed_fields",
                confidence=parsed_track.confidence,
                explanation="Built from parsed artist and title fields.",
            )
        elif parsed_track.title:
            self._append_variant(
                variants=variants,
                text=parsed_track.title,
                source="parsed_title",
                confidence=parsed_track.confidence,
                explanation="Built from parsed title because artist is unknown.",
            )

        for alias_variant in self._alias_expander.expand(
            parsed_track.artist,
            parsed_track.title,
        ):
            self._append_variant(
                variants=variants,
                text=alias_variant,
                source="artist_alias",
                confidence=max(parsed_track.confidence, 0.95),
                explanation="Built from a known artist alias.",
            )

        if parsed_track.normalized_input:
            self._append_variant(
                variants=variants,
                text=parsed_track.normalized_input,
                source="normalized_input",
                confidence=max(parsed_track.confidence * 0.8, 0.1),
                explanation="Built from the full normalized input line.",
            )

        for transliteration_candidate in parsed_track.transliteration_candidates:
            self._append_variant(
                variants=variants,
                text=transliteration_candidate.text,
                source=f"transliteration:{transliteration_candidate.direction.value}",
                confidence=transliteration_candidate.confidence,
                explanation=transliteration_candidate.explanation,
            )

        return tuple(variants)

    def _append_variant(
        self,
        variants: list[MatchQueryVariant],
        text: str,
        source: str,
        confidence: float,
        explanation: str,
    ) -> None:
        compacted_text = " ".join(text.strip().split())
        if not compacted_text:
            return

        if any(
            variant.text.casefold() == compacted_text.casefold() for variant in variants
        ):
            return

        variants.append(
            MatchQueryVariant(
                text=compacted_text,
                source=source,
                confidence=round(confidence, 4),
                explanation=explanation,
            )
        )

    def _rank_and_deduplicate(
        self,
        matches: Sequence[MatchResult],
    ) -> list[MatchResult]:
        best_by_candidate: dict[tuple[str, str], MatchResult] = {}

        for match in matches:
            candidate_key = (match.source, match.track_id)
            current_best = best_by_candidate.get(candidate_key)
            if current_best is None or self._is_better(match, current_best):
                best_by_candidate[candidate_key] = match

        return sorted(
            best_by_candidate.values(),
            key=lambda match: (
                match.score,
                match.query_variant_confidence,
                -match.distance,
                match.candidate.display_text,
            ),
            reverse=True,
        )

    def _is_better(self, candidate: MatchResult, current_best: MatchResult) -> bool:
        candidate_key = (
            candidate.score,
            candidate.query_variant_confidence,
            -candidate.distance,
        )
        current_key = (
            current_best.score,
            current_best.query_variant_confidence,
            -current_best.distance,
        )
        return candidate_key > current_key

"""Evaluation helpers for matcher baseline experiments."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.core.catalog import InMemoryTrackCatalog
from backend.core.matcher.base import BaseMatcher
from backend.core.matcher.hybrid import HybridMatcher
from backend.core.matcher.jaro_winkler import JaroWinklerMatcher
from backend.core.matcher.levenshtein import LevenshteinMatcher
from backend.core.matcher.schemas import MatchResult, TrackCandidate
from backend.core.search import DemoTrackSearchProvider, TrackSearchService

SUPPORTED_MATCHERS = {
    "hybrid": HybridMatcher,
    "levenshtein": LevenshteinMatcher,
    "jaro_winkler": JaroWinklerMatcher,
}


class MatcherEvaluationExample(BaseModel):
    """One labeled matcher example from a research dataset."""

    model_config = ConfigDict(frozen=True)

    query: str = Field(description="Search query to evaluate.")
    expected_track_id: str = Field(description="Expected top matching track id.")
    notes: str | None = Field(default=None, description="Dataset annotation notes.")


class MatcherEvaluationCaseResult(BaseModel):
    """Evaluation result for one matcher example."""

    model_config = ConfigDict(frozen=True)

    example: MatcherEvaluationExample = Field(description="Labeled query example.")
    matches: tuple[MatchResult, ...] = Field(description="Ranked matcher results.")
    top_1_matched: bool = Field(description="Whether top-1 matched the label.")
    top_k_matched: bool = Field(description="Whether top-k matched the label.")
    top_1_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Top-1 score, or 0 when there is no match.",
    )
    runner_up_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Top-2 score, or 0 when there is no runner-up.",
    )
    score_margin: float = Field(
        ge=0.0,
        le=1.0,
        description="Difference between top-1 and runner-up scores.",
    )
    is_ambiguous: bool = Field(
        description="Whether the top match is close to the runner-up."
    )


class MatcherEvaluationReport(BaseModel):
    """Aggregate matcher evaluation metrics."""

    model_config = ConfigDict(frozen=True)

    total: int = Field(ge=0, description="Number of evaluated examples.")
    k: int = Field(ge=1, description="Top-k cutoff used by the report.")
    top_1_accuracy: float = Field(ge=0.0, le=1.0)
    top_k_accuracy: float = Field(ge=0.0, le=1.0)
    ambiguous_count: int = Field(ge=0, description="Number of ambiguous cases.")
    case_results: tuple[MatcherEvaluationCaseResult, ...] = Field(
        description="Per-example evaluation results."
    )


class MatcherComparisonReport(BaseModel):
    """Comparison report for multiple matcher algorithms."""

    model_config = ConfigDict(frozen=True)

    reports: tuple[MatcherEvaluationReport, ...] = Field(
        description="Matcher reports in comparison order."
    )


class MatcherEvaluator:
    """Evaluate candidate search and matching accuracy against labels."""

    def __init__(
        self,
        search_service: TrackSearchService,
        matcher: BaseMatcher | None = None,
    ) -> None:
        self._search_service = search_service
        self._matcher = matcher or LevenshteinMatcher()

    async def evaluate(
        self,
        examples: Sequence[MatcherEvaluationExample],
        *,
        k: int = 3,
        ambiguity_margin_threshold: float = 0.05,
    ) -> MatcherEvaluationReport:
        """Evaluate top-1 and top-k accuracy for labeled matcher examples."""
        case_results = tuple(
            [
                await self._evaluate_one(
                    example=example,
                    k=k,
                    ambiguity_margin_threshold=ambiguity_margin_threshold,
                )
                for example in examples
            ]
        )
        total = len(case_results)

        if total == 0:
            return MatcherEvaluationReport(
                total=0,
                k=k,
                top_1_accuracy=0.0,
                top_k_accuracy=0.0,
                ambiguous_count=0,
                case_results=(),
            )

        return MatcherEvaluationReport(
            total=total,
            k=k,
            top_1_accuracy=self._ratio(
                sum(result.top_1_matched for result in case_results),
                total,
            ),
            top_k_accuracy=self._ratio(
                sum(result.top_k_matched for result in case_results),
                total,
            ),
            ambiguous_count=sum(result.is_ambiguous for result in case_results),
            case_results=case_results,
        )

    async def _evaluate_one(
        self,
        example: MatcherEvaluationExample,
        k: int,
        ambiguity_margin_threshold: float,
    ) -> MatcherEvaluationCaseResult:
        search_result = await self._search_service.search(
            query=example.query,
            limit_per_source=k,
        )
        matches = tuple(
            self._matcher.match(
                query=example.query,
                candidates=search_result.candidates,
                limit=k,
            )
        )
        matched_track_ids = {match.track_id for match in matches}
        top_match = matches[0] if matches else None
        runner_up_match = matches[1] if len(matches) > 1 else None
        top_1_score = top_match.score if top_match is not None else 0.0
        runner_up_score = runner_up_match.score if runner_up_match is not None else 0.0
        score_margin = round(top_1_score - runner_up_score, 4)

        return MatcherEvaluationCaseResult(
            example=example,
            matches=matches,
            top_1_matched=(
                top_match is not None
                and top_match.track_id == example.expected_track_id
            ),
            top_k_matched=example.expected_track_id in matched_track_ids,
            top_1_score=top_1_score,
            runner_up_score=runner_up_score,
            score_margin=score_margin,
            is_ambiguous=(
                runner_up_match is not None
                and score_margin <= ambiguity_margin_threshold
            ),
        )

    def _ratio(self, numerator: int, denominator: int) -> float:
        return round(numerator / denominator, 4)


def load_track_candidates(dataset_path: Path) -> list[TrackCandidate]:
    """Load track candidates from a JSON Lines dataset."""
    return [
        TrackCandidate.model_validate(raw_item)
        for raw_item in _load_jsonl(dataset_path)
    ]


def load_labeled_matcher_examples(
    dataset_path: Path,
) -> list[MatcherEvaluationExample]:
    """Load labeled matcher examples from a JSON Lines dataset."""
    return [
        MatcherEvaluationExample.model_validate(raw_item)
        for raw_item in _load_jsonl(dataset_path)
    ]


def build_matcher_evaluation_summary(report: MatcherEvaluationReport) -> str:
    """Build a compact text summary for CLI usage."""
    return (
        f"total={report.total} "
        f"k={report.k} "
        f"top_1_accuracy={report.top_1_accuracy:.4f} "
        f"top_k_accuracy={report.top_k_accuracy:.4f} "
        f"ambiguous_count={report.ambiguous_count}"
    )


async def evaluate_default_dataset(
    examples_path: Path,
    candidates_path: Path,
    *,
    k: int,
    algorithm: str = "levenshtein",
) -> MatcherEvaluationReport:
    """Evaluate matcher against local JSONL datasets."""
    examples = load_labeled_matcher_examples(examples_path)
    candidates = load_track_candidates(candidates_path)
    search_service = TrackSearchService(
        [DemoTrackSearchProvider(InMemoryTrackCatalog(candidates))]
    )
    matcher = build_matcher(algorithm)

    return await MatcherEvaluator(
        search_service=search_service, matcher=matcher
    ).evaluate(
        examples,
        k=k,
    )


async def compare_matchers_on_default_dataset(
    examples_path: Path,
    candidates_path: Path,
    *,
    k: int,
    algorithms: Sequence[str] | None = None,
) -> MatcherComparisonReport:
    """Evaluate multiple matcher algorithms on the same local datasets."""
    selected_algorithms = tuple(algorithms or sorted(SUPPORTED_MATCHERS))
    reports: list[MatcherEvaluationReport] = []

    for algorithm in selected_algorithms:
        report = await evaluate_default_dataset(
            examples_path=examples_path,
            candidates_path=candidates_path,
            k=k,
            algorithm=algorithm,
        )
        reports.append(report)

    return MatcherComparisonReport(reports=tuple(reports))


def build_matcher(algorithm: str) -> BaseMatcher:
    """Build a matcher by stable algorithm name."""
    matcher_class = SUPPORTED_MATCHERS.get(algorithm)
    if matcher_class is None:
        supported = ", ".join(sorted(SUPPORTED_MATCHERS))
        msg = f"Unsupported matcher algorithm '{algorithm}'. Supported: {supported}."
        raise ValueError(msg)

    return matcher_class()


def build_matcher_comparison_summary(report: MatcherComparisonReport) -> str:
    """Build a compact table-like summary for matcher comparison."""
    lines = ["algorithm\ttotal\tk\ttop_1_accuracy\ttop_k_accuracy\tambiguous_count"]
    for matcher_report in report.reports:
        algorithm = (
            matcher_report.case_results[0].matches[0].algorithm
            if matcher_report.case_results and matcher_report.case_results[0].matches
            else "unknown"
        )
        lines.append(
            f"{algorithm}\t{matcher_report.total}\t{matcher_report.k}\t"
            f"{matcher_report.top_1_accuracy:.4f}\t"
            f"{matcher_report.top_k_accuracy:.4f}\t"
            f"{matcher_report.ambiguous_count}"
        )

    return "\n".join(lines)


def _load_jsonl(dataset_path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    with dataset_path.open(encoding="utf-8") as dataset_file:
        for line_number, line in enumerate(dataset_file, start=1):
            stripped_line = line.strip()
            if not stripped_line:
                continue

            try:
                raw_item = json.loads(stripped_line)
            except json.JSONDecodeError as exc:
                msg = f"Invalid JSON on line {line_number} in {dataset_path}."
                raise ValueError(msg) from exc

            if not isinstance(raw_item, dict):
                msg = f"Expected JSON object on line {line_number} in {dataset_path}."
                raise ValueError(msg)

            items.append(raw_item)

    return items


def main() -> None:
    """Run matcher evaluation from the command line."""
    argument_parser = argparse.ArgumentParser(
        description="Evaluate matcher baseline against local JSONL datasets."
    )
    argument_parser.add_argument(
        "--examples",
        type=Path,
        default=Path("datasets/matcher/labeled_queries.jsonl"),
        help="Path to a JSON Lines matcher examples dataset.",
    )
    argument_parser.add_argument(
        "--candidates",
        type=Path,
        default=Path("datasets/matcher/candidates.jsonl"),
        help="Path to a JSON Lines candidates dataset.",
    )
    argument_parser.add_argument(
        "--k",
        type=int,
        default=3,
        help="Top-k cutoff.",
    )
    argument_parser.add_argument(
        "--algorithm",
        choices=sorted(SUPPORTED_MATCHERS),
        default="levenshtein",
        help="Matcher algorithm to evaluate.",
    )
    argument_parser.add_argument(
        "--compare-all",
        action="store_true",
        help="Evaluate all supported matcher algorithms and print a comparison table.",
    )
    args = argument_parser.parse_args()

    import asyncio

    if args.compare_all:
        comparison_report = asyncio.run(
            compare_matchers_on_default_dataset(
                examples_path=args.examples,
                candidates_path=args.candidates,
                k=args.k,
            )
        )
        print(build_matcher_comparison_summary(comparison_report))
        return

    report = asyncio.run(
        evaluate_default_dataset(
            examples_path=args.examples,
            candidates_path=args.candidates,
            k=args.k,
            algorithm=args.algorithm,
        )
    )
    print(build_matcher_evaluation_summary(report))


if __name__ == "__main__":
    main()

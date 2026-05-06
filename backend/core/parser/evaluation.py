"""Evaluation helpers for parser baseline experiments."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.core.parser.pipeline import TrackParsingPipeline
from backend.core.parser.schemas import ParsedTrack, TrackPattern


class ParserEvaluationExample(BaseModel):
    """One labeled parser example from a research dataset."""

    model_config = ConfigDict(frozen=True)

    raw_input: str = Field(description="Raw track line to parse.")
    expected_artist: str | None = Field(description="Expected parsed artist.")
    expected_title: str | None = Field(description="Expected parsed title.")
    expected_pattern: TrackPattern = Field(description="Expected parser pattern.")
    notes: str | None = Field(default=None, description="Dataset annotation notes.")


class ParserEvaluationCaseResult(BaseModel):
    """Evaluation result for one labeled parser example."""

    model_config = ConfigDict(frozen=True)

    example: ParserEvaluationExample = Field(description="Labeled input example.")
    parsed_track: ParsedTrack = Field(description="Actual parser output.")
    artist_matched: bool = Field(description="Whether artist matched the label.")
    title_matched: bool = Field(description="Whether title matched the label.")
    pattern_matched: bool = Field(description="Whether pattern matched the label.")
    exact_match: bool = Field(description="Whether all evaluated fields matched.")


class ParserEvaluationReport(BaseModel):
    """Aggregate parser evaluation metrics."""

    model_config = ConfigDict(frozen=True)

    total: int = Field(ge=0, description="Number of evaluated examples.")
    artist_accuracy: float = Field(ge=0.0, le=1.0)
    title_accuracy: float = Field(ge=0.0, le=1.0)
    pattern_accuracy: float = Field(ge=0.0, le=1.0)
    exact_match_accuracy: float = Field(ge=0.0, le=1.0)
    case_results: tuple[ParserEvaluationCaseResult, ...] = Field(
        description="Per-example evaluation results."
    )


class ParserEvaluator:
    """Evaluate parser output against labeled examples."""

    def __init__(self, parser: TrackParsingPipeline | None = None) -> None:
        self._parser = parser or TrackParsingPipeline()

    def evaluate(
        self,
        examples: Sequence[ParserEvaluationExample],
    ) -> ParserEvaluationReport:
        """Evaluate parser accuracy for a sequence of labeled examples."""
        case_results = tuple(self._evaluate_one(example) for example in examples)
        total = len(case_results)

        if total == 0:
            return ParserEvaluationReport(
                total=0,
                artist_accuracy=0.0,
                title_accuracy=0.0,
                pattern_accuracy=0.0,
                exact_match_accuracy=0.0,
                case_results=(),
            )

        return ParserEvaluationReport(
            total=total,
            artist_accuracy=self._ratio(
                sum(result.artist_matched for result in case_results),
                total,
            ),
            title_accuracy=self._ratio(
                sum(result.title_matched for result in case_results),
                total,
            ),
            pattern_accuracy=self._ratio(
                sum(result.pattern_matched for result in case_results),
                total,
            ),
            exact_match_accuracy=self._ratio(
                sum(result.exact_match for result in case_results),
                total,
            ),
            case_results=case_results,
        )

    def _evaluate_one(
        self,
        example: ParserEvaluationExample,
    ) -> ParserEvaluationCaseResult:
        parsed_track = self._parser.parse_line(example.raw_input)
        artist_matched = self._values_equal(
            parsed_track.artist,
            example.expected_artist,
        )
        title_matched = self._values_equal(
            parsed_track.title,
            example.expected_title,
        )
        pattern_matched = parsed_track.pattern == example.expected_pattern

        return ParserEvaluationCaseResult(
            example=example,
            parsed_track=parsed_track,
            artist_matched=artist_matched,
            title_matched=title_matched,
            pattern_matched=pattern_matched,
            exact_match=artist_matched and title_matched and pattern_matched,
        )

    def _values_equal(self, actual: str | None, expected: str | None) -> bool:
        if actual is None or expected is None:
            return actual == expected

        return self._normalize_for_comparison(actual) == self._normalize_for_comparison(
            expected
        )

    def _normalize_for_comparison(self, value: str) -> str:
        return " ".join(value.casefold().strip().split())

    def _ratio(self, numerator: int, denominator: int) -> float:
        return round(numerator / denominator, 4)


def load_labeled_parser_examples(
    dataset_path: Path,
) -> list[ParserEvaluationExample]:
    """Load labeled parser examples from a JSON Lines dataset."""
    examples: list[ParserEvaluationExample] = []

    with dataset_path.open(encoding="utf-8") as dataset_file:
        for line_number, line in enumerate(dataset_file, start=1):
            stripped_line = line.strip()
            if not stripped_line:
                continue

            try:
                raw_example: Any = json.loads(stripped_line)
            except json.JSONDecodeError as exc:
                msg = f"Invalid JSON on line {line_number} in {dataset_path}."
                raise ValueError(msg) from exc

            examples.append(ParserEvaluationExample.model_validate(raw_example))

    return examples


def build_parser_evaluation_summary(report: ParserEvaluationReport) -> str:
    """Build a compact text summary for CLI usage."""
    return (
        f"total={report.total} "
        f"artist_accuracy={report.artist_accuracy:.4f} "
        f"title_accuracy={report.title_accuracy:.4f} "
        f"pattern_accuracy={report.pattern_accuracy:.4f} "
        f"exact_match_accuracy={report.exact_match_accuracy:.4f}"
    )


def main() -> None:
    """Run parser evaluation from the command line."""
    argument_parser = argparse.ArgumentParser(
        description="Evaluate the parser baseline against a JSONL dataset."
    )
    argument_parser.add_argument(
        "dataset_path",
        nargs="?",
        type=Path,
        default=Path("datasets/parser/labeled_tracks.jsonl"),
        help="Path to a JSON Lines parser dataset.",
    )
    args = argument_parser.parse_args()

    examples = load_labeled_parser_examples(args.dataset_path)
    report = ParserEvaluator().evaluate(examples)
    print(build_parser_evaluation_summary(report))


if __name__ == "__main__":
    main()

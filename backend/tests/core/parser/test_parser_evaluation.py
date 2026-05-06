from pathlib import Path

from backend.core.parser import TrackPattern
from backend.core.parser.evaluation import (
    ParserEvaluationExample,
    ParserEvaluator,
    build_parser_evaluation_summary,
    load_labeled_parser_examples,
)

DATASET_PATH = Path("datasets/parser/labeled_tracks.jsonl")


def test_evaluates_parser_examples() -> None:
    examples = [
        ParserEvaluationExample(
            raw_input="Daft Punk - Around the World",
            expected_artist="daft punk",
            expected_title="around the world",
            expected_pattern=TrackPattern.ARTIST_TITLE,
        ),
        ParserEvaluationExample(
            raw_input="Unknown floating track name",
            expected_artist=None,
            expected_title="unknown floating track name",
            expected_pattern=TrackPattern.UNKNOWN,
        ),
    ]

    report = ParserEvaluator().evaluate(examples)

    assert report.total == 2
    assert report.artist_accuracy == 1.0
    assert report.title_accuracy == 1.0
    assert report.pattern_accuracy == 1.0
    assert report.exact_match_accuracy == 1.0


def test_loads_labeled_parser_examples_from_jsonl() -> None:
    examples = load_labeled_parser_examples(DATASET_PATH)

    assert len(examples) == 10
    assert examples[0].raw_input == "Daft Punk - Around the World"
    assert examples[0].expected_pattern == TrackPattern.ARTIST_TITLE


def test_builds_compact_evaluation_summary() -> None:
    examples = [
        ParserEvaluationExample(
            raw_input="Bonobo - Kerala",
            expected_artist="bonobo",
            expected_title="kerala",
            expected_pattern=TrackPattern.ARTIST_TITLE,
        )
    ]
    report = ParserEvaluator().evaluate(examples)

    summary = build_parser_evaluation_summary(report)

    assert summary == (
        "total=1 artist_accuracy=1.0000 title_accuracy=1.0000 "
        "pattern_accuracy=1.0000 exact_match_accuracy=1.0000"
    )

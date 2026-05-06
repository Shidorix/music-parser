from pathlib import Path

import pytest

from backend.core.matcher.evaluation import (
    MatcherEvaluator,
    build_matcher_evaluation_summary,
    build_matcher_comparison_summary,
    compare_matchers_on_default_dataset,
    evaluate_default_dataset,
    load_labeled_matcher_examples,
    load_track_candidates,
)
from backend.core.search import DemoTrackSearchProvider, TrackSearchService
from backend.core.catalog import InMemoryTrackCatalog

CANDIDATES_PATH = Path("datasets/matcher/candidates.jsonl")
EXAMPLES_PATH = Path("datasets/matcher/labeled_queries.jsonl")


@pytest.mark.asyncio
async def test_evaluates_default_matcher_dataset() -> None:
    report = await evaluate_default_dataset(
        examples_path=EXAMPLES_PATH,
        candidates_path=CANDIDATES_PATH,
        k=3,
    )

    assert report.total >= 10
    assert report.k == 3
    assert report.top_1_accuracy >= 0.7
    assert report.top_k_accuracy >= report.top_1_accuracy
    assert report.ambiguous_count >= 0
    assert report.case_results[0].score_margin >= 0.0


def test_loads_matcher_datasets() -> None:
    candidates = load_track_candidates(CANDIDATES_PATH)
    examples = load_labeled_matcher_examples(EXAMPLES_PATH)

    assert len(candidates) >= 10
    assert len(examples) >= 10
    assert candidates[0].track_id == "demo:daft-punk-around-the-world"


@pytest.mark.asyncio
async def test_builds_matcher_evaluation_summary() -> None:
    candidates = load_track_candidates(CANDIDATES_PATH)
    examples = load_labeled_matcher_examples(EXAMPLES_PATH)
    report = await MatcherEvaluator(
        TrackSearchService([DemoTrackSearchProvider(InMemoryTrackCatalog(candidates))])
    ).evaluate(examples[:1], k=3)

    assert build_matcher_evaluation_summary(report) == (
        "total=1 k=3 top_1_accuracy=1.0000 top_k_accuracy=1.0000 " "ambiguous_count=0"
    )


@pytest.mark.asyncio
async def test_compares_supported_matchers() -> None:
    report = await compare_matchers_on_default_dataset(
        examples_path=EXAMPLES_PATH,
        candidates_path=CANDIDATES_PATH,
        k=3,
        algorithms=("levenshtein", "jaro_winkler"),
    )

    summary = build_matcher_comparison_summary(report)

    assert len(report.reports) == 2
    assert (
        "algorithm\ttotal\tk\ttop_1_accuracy\ttop_k_accuracy\tambiguous_count"
        in summary
    )
    assert "levenshtein" in summary
    assert "jaro_winkler" in summary

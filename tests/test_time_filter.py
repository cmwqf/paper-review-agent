"""Purpose: Tests for retrieval time filtering."""

from datetime import date

from reviewer.retrieval.time_filter import filter_before_submission
from reviewer.retrieval.types import RetrievedPaper


def test_filter_before_submission_drops_future_papers() -> None:
    """Future papers should not influence a review."""
    papers = [
        RetrievedPaper(title="old", publication_date=date(2024, 1, 1)),
        RetrievedPaper(title="future", publication_date=date(2026, 1, 1)),
    ]
    filtered = filter_before_submission(papers, date(2025, 1, 1))
    assert [paper.title for paper in filtered] == ["old"]


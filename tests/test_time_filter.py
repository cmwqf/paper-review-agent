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


def test_filter_before_submission_drops_future_year_without_publication_date() -> None:
    """Future-year papers should be dropped even when publicationDate is missing."""
    papers = [
        RetrievedPaper(title="old year", year=2023, publication_date=None),
        RetrievedPaper(title="future year", year=2026, publication_date=None),
        RetrievedPaper(title="unknown date", year=None, publication_date=None),
    ]
    filtered = filter_before_submission(papers, date(2024, 1, 1))
    assert [paper.title for paper in filtered] == ["old year", "unknown date"]

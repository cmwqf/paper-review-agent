"""Purpose: Filter retrieved papers by publication date relative to submission time."""

from __future__ import annotations

from datetime import date

from reviewer.retrieval.types import RetrievedPaper


def filter_before_submission(
    papers: list[RetrievedPaper], submission_date: date | None
) -> list[RetrievedPaper]:
    """Drop papers published after the reviewed paper's submission date."""
    if submission_date is None:
        return papers
    return [
        paper
        for paper in papers
        if _is_not_after_submission(paper, submission_date)
    ]


def _is_not_after_submission(paper: RetrievedPaper, submission_date: date) -> bool:
    """Use full publication date when available, otherwise fall back to year."""
    if paper.publication_date is not None:
        return paper.publication_date <= submission_date
    if paper.year is not None:
        return int(paper.year) <= submission_date.year
    return True

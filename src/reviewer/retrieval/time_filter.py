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
        if paper.publication_date is None or paper.publication_date <= submission_date
    ]


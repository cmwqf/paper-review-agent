"""Purpose: Typed data structures for retrieval queries and retrieved papers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class RetrievedPaper:
    """A normalized paper returned by scholarly search."""

    title: str
    abstract: str | None = None
    year: int | None = None
    publication_date: date | None = None
    url: str | None = None
    citation_count: int | None = None


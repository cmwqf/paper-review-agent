"""Purpose: Scaffold for searching within the reviewed paper.

PaperSearchTool is a local evidence-navigation tool. It should accept a query
such as "baselines and ablations" and return ranked paper chunk references with
short snippets. It should not return long raw chunks by default.

Planned responsibilities:

- search section titles, chunk text, and metadata
- return chunk_id / section_id / score / snippet
- keep results compact for Agent context
- support a future upgrade from keyword search to embedding retrieval
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PaperSearchResult:
    """Compact reference to a paper chunk found by paper-local search."""

    chunk_id: str
    snippet: str
    score: float | None = None
    section_id: str | None = None
    section_title: str | None = None


class PaperSearchTool:
    """Search the reviewed paper and return compact chunk references."""

    def __init__(self, config: dict):
        self.config = config

    def search(self, query: str, paper: dict, top_k: int = 5) -> list[PaperSearchResult]:
        """Return compact references to relevant paper chunks."""
        raise NotImplementedError("PaperSearchTool.search is scaffolded.")


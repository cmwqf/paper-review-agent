"""Purpose: Orchestrate query generation, Semantic Scholar search, filtering, and reranking."""

from __future__ import annotations


class RetrievalTool:
    """Shared retrieval interface used by Q&A answering."""

    def __init__(self, config: dict):
        self.config = config

    def search(self, question: str, paper_metadata: dict) -> list[dict]:
        """Return reranked papers relevant to a review question."""
        raise NotImplementedError("RetrievalTool.search is scaffolded.")


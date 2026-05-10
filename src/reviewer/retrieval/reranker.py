"""Purpose: Rerank retrieved papers by relevance to the review question."""

from __future__ import annotations

from reviewer.retrieval.types import RetrievedPaper


class Reranker:
    """Wrapper for local or remote reranker models."""

    def __init__(self, config: dict):
        self.config = config

    def rerank(self, query: str, papers: list[RetrievedPaper], top_k: int) -> list[RetrievedPaper]:
        """Return top-k papers; scaffold keeps original order."""
        return papers[:top_k]


"""Purpose: Client for local or remote reranker endpoints."""

from __future__ import annotations


class RerankerClient:
    """Reranker service placeholder."""

    def __init__(self, model_config: dict):
        self.model_config = model_config

    def score(self, query: str, documents: list[str]) -> list[float]:
        """Score query-document relevance."""
        raise NotImplementedError("RerankerClient.score is scaffolded.")


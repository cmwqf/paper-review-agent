"""Purpose: Semantic Scholar API client for retrieving related papers."""

from __future__ import annotations


class SemanticScholarClient:
    """Thin client around Semantic Scholar Graph API."""

    def __init__(self, config: dict):
        self.config = config

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Search Semantic Scholar for one query."""
        raise NotImplementedError("SemanticScholarClient.search is scaffolded.")


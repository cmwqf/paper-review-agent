"""Purpose: Semantic Scholar API client for retrieving related papers."""

from __future__ import annotations

import os
from datetime import date
from typing import Any

import requests

from reviewer.retrieval.types import RetrievedPaper


class SemanticScholarClient:
    """Thin client around Semantic Scholar Graph API."""

    def __init__(self, config: dict):
        self.config = config

    def search(self, query: str, limit: int = 20) -> list[RetrievedPaper]:
        """Search Semantic Scholar for one query."""
        provider_config = self.config.get("retrieval", {}).get("semantic_scholar", {})
        endpoint = provider_config.get(
            "endpoint", "https://api.semanticscholar.org/graph/v1/paper/search"
        )
        fields = provider_config.get(
            "fields",
            [
                "title",
                "abstract",
                "year",
                "authors",
                "venue",
                "citationCount",
                "publicationDate",
                "externalIds",
                "url",
            ],
        )
        timeout = float(provider_config.get("timeout_seconds", 30))
        headers = {}
        api_key_env = provider_config.get("api_key_env")
        if api_key_env and os.environ.get(str(api_key_env)):
            headers["x-api-key"] = os.environ[str(api_key_env)]

        response = requests.get(
            str(endpoint),
            params={"query": query, "limit": limit, "fields": ",".join(fields)},
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        return [_normalize_paper(item) for item in data.get("data", []) if item.get("title")]


def _parse_date(value: Any) -> date | None:
    """Parse Semantic Scholar publicationDate values."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _normalize_paper(item: dict[str, Any]) -> RetrievedPaper:
    """Normalize one Semantic Scholar item into RetrievedPaper."""
    return RetrievedPaper(
        title=str(item.get("title") or ""),
        abstract=item.get("abstract"),
        year=item.get("year"),
        publication_date=_parse_date(item.get("publicationDate")),
        url=item.get("url"),
        citation_count=item.get("citationCount"),
    )

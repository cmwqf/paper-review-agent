"""Purpose: Semantic Scholar API client for retrieving related papers."""

from __future__ import annotations

import logging
import os
import time
from datetime import date
from typing import Any

import requests

from reviewer.retrieval.types import RetrievedPaper

LOGGER = logging.getLogger(__name__)


class SemanticScholarClient:
    """Thin client around Semantic Scholar Graph API."""

    def __init__(self, config: dict):
        self.config = config

    def _provider_config(self) -> dict:
        """Return the semantic_scholar provider config block."""
        return self.config.get("retrieval", {}).get("semantic_scholar", {})

    def _headers(self) -> dict[str, str]:
        """Build request headers, including the API key when configured."""
        headers: dict[str, str] = {}
        api_key_env = self._provider_config().get("api_key_env")
        if api_key_env and os.environ.get(str(api_key_env)):
            headers["x-api-key"] = os.environ[str(api_key_env)]
        return headers

    def _paper_base(self) -> str:
        """Resolve the `.../graph/v1/paper` base URL from the search endpoint."""
        endpoint = str(
            self._provider_config().get(
                "endpoint", "https://api.semanticscholar.org/graph/v1/paper/search"
            )
        )
        return endpoint.rstrip("/").removesuffix("/search")

    def _get_with_backoff(self, url: str, params: dict) -> requests.Response | None:
        """GET with retry/backoff on 429. Returns None only on a 404 (no match)."""
        timeout = float(self._provider_config().get("timeout_seconds", 30))
        max_retries = int(self._provider_config().get("match_max_retries", 4))
        headers = self._headers()
        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=timeout)
            except requests.RequestException as exc:
                last_exc = exc
                time.sleep(2 * (attempt + 1))
                continue
            if response.status_code == 404:
                return None
            if response.status_code == 429:
                LOGGER.info("Semantic Scholar rate-limited (429); backing off attempt %s.", attempt + 1)
                time.sleep(3 + 2 * attempt)
                continue
            response.raise_for_status()
            return response
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Semantic Scholar match exhausted retries (rate-limited).")

    def match(self, title: str) -> dict[str, Any] | None:
        """Return the single best title match, or None when no paper matches.

        Uses the `/paper/search/match` endpoint, which returns a 404 when the
        title has no close match in the corpus — the core existence signal for
        citation-integrity checks. Raises on persistent rate-limiting so callers
        can treat that distinctly from a confirmed "no match".
        """
        url = f"{self._paper_base()}/search/match"
        fields = "title,year,authors,venue,externalIds,url"
        response = self._get_with_backoff(url, {"query": title, "fields": fields})
        if response is None:
            return None
        data = response.json().get("data", [])
        return data[0] if data else None

    def lookup_external_id(self, id_type: str, id_value: str) -> dict[str, Any] | None:
        """Look up a paper by external id (e.g. ARXIV, DOI); None if not found."""
        url = f"{self._paper_base()}/{id_type}:{id_value}"
        response = self._get_with_backoff(url, {"fields": "title,year,externalIds,url"})
        if response is None:
            return None
        return response.json()

    def search(self, query: str, limit: int = 20) -> list[RetrievedPaper]:
        """Search Semantic Scholar for one query."""
        provider_config = self.config.get("retrieval", {}).get("semantic_scholar", {})
        endpoint = provider_config.get(
            "endpoint", "https://api.semanticscholar.org/graph/v1/paper/search"
        )
        fields = (
            provider_config.get("fields")
            or self.config.get("retrieval", {}).get("search", {}).get("fields")
            or [
                "title",
                "abstract",
                "year",
                "authors",
                "venue",
                "citationCount",
                "publicationDate",
                "externalIds",
                "url",
            ]
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

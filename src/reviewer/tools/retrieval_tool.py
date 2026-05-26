"""Purpose: Orchestrate Semantic Scholar search, filtering, and reranking."""

from __future__ import annotations

import logging
from datetime import date

from reviewer.retrieval.reranker import Reranker
from reviewer.retrieval.semantic_scholar import SemanticScholarClient
from reviewer.retrieval.time_filter import filter_before_submission
from reviewer.retrieval.types import RetrievedPaper

LOGGER = logging.getLogger(__name__)


class RetrievalTool:
    """Shared retrieval interface used by Q&A answering."""

    def __init__(self, config: dict):
        self.config = config
        self.client = SemanticScholarClient(config)

    def search(self, query: str, paper_metadata: dict) -> list[dict]:
        """Return retrieved papers for the exact query chosen by the Answer Agent."""
        if not self.config.get("retrieval", {}).get("enabled", True):
            return []
        query = query.strip()
        if not query:
            return []
        limit = int(self.config.get("retrieval", {}).get("search", {}).get("limit_per_query", 10))
        try:
            papers = self.client.search(query, limit=limit)
        except Exception as exc:
            LOGGER.warning("Semantic Scholar search failed for query %r: %s", query, exc)
            return []

        submission_date = _submission_date(paper_metadata)
        if self.config.get("retrieval", {}).get("time_filter", {}).get("enabled", True):
            papers = filter_before_submission(papers, submission_date)
        papers = self._rerank_if_enabled(query, papers)
        return [_paper_to_dict(paper) for paper in papers]

    def _rerank_if_enabled(self, query: str, papers: list[RetrievedPaper]) -> list[RetrievedPaper]:
        """Optionally rerank retrieved papers with a chat-completion model."""
        rerank_config = self.config.get("retrieval", {}).get("rerank", {})
        if not rerank_config.get("enabled", False):
            return papers
        min_candidates = int(rerank_config.get("min_candidates", 2))
        top_k = int(rerank_config.get("top_k", len(papers)))
        if len(papers) < min_candidates:
            return papers[:top_k]
        return Reranker(self.config).rerank(query, papers, top_k=top_k)


def _submission_date(metadata: dict) -> date | None:
    """Read a submission date from normalized paper metadata."""
    raw = metadata.get("submission_date") or metadata.get("date")
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw))
    except ValueError:
        return None


def _paper_to_dict(paper: RetrievedPaper) -> dict:
    """Serialize RetrievedPaper for prompts and traces."""
    return {
        "title": paper.title,
        "abstract": paper.abstract,
        "year": paper.year,
        "publication_date": paper.publication_date.isoformat() if paper.publication_date else None,
        "url": paper.url,
        "citation_count": paper.citation_count,
    }

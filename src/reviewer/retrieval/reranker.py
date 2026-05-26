"""Purpose: Rerank retrieved papers by relevance to the review question."""

from __future__ import annotations

import logging

from reviewer.models.factory import build_reranker
from reviewer.retrieval.types import RetrievedPaper

LOGGER = logging.getLogger(__name__)


class Reranker:
    """Wrapper for chat-completion reranking of retrieved papers."""

    def __init__(self, config: dict):
        self.config = config
        rerank_config = config.get("retrieval", {}).get("rerank", {})
        model_key = rerank_config.get("model", "reranker")
        self.client = build_reranker(config, str(model_key))

    def rerank(self, query: str, papers: list[RetrievedPaper], top_k: int) -> list[RetrievedPaper]:
        """Return top-k papers ordered by model-assessed relevance.

        If the reranker fails or returns an incomplete ordering, keep available
        model-ranked papers first and preserve original order for the rest.
        """
        if not papers:
            return []
        candidates = [
            {
                "id": f"R{index}",
                "title": paper.title,
                "year": str(paper.year or ""),
                "abstract": _truncate(paper.abstract or ""),
            }
            for index, paper in enumerate(papers, start=1)
        ]
        paper_by_id = dict(zip((candidate["id"] for candidate in candidates), papers))
        try:
            ranked_ids = self.client.rank(query, candidates)
        except Exception as exc:
            LOGGER.warning("Reranker failed for query %r: %s", query, exc)
            return papers[:top_k]

        ranked: list[RetrievedPaper] = []
        seen: set[str] = set()
        for candidate_id in ranked_ids:
            paper = paper_by_id.get(candidate_id)
            if paper is not None and candidate_id not in seen:
                ranked.append(paper)
                seen.add(candidate_id)
        for candidate, paper in zip(candidates, papers):
            if candidate["id"] not in seen:
                ranked.append(paper)
        return ranked[:top_k]


def _truncate(text: str, max_chars: int = 1200) -> str:
    """Keep reranker prompts bounded without dropping titles or IDs."""
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars].rstrip()}..."

"""Purpose: Chat-completion client for ranking retrieved papers."""

from __future__ import annotations

import json
import re
from typing import Any

from reviewer.models.claude_code_client import make_text_client


class RerankerClient:
    """Use a chat model (HTTP API or Claude Code CLI) to rank candidate paper IDs."""

    def __init__(self, model_config: dict, global_config: dict | None = None):
        self.model_config = model_config
        self.client = make_text_client(model_config, global_config=global_config)

    def rank(self, query: str, candidates: list[dict[str, str]]) -> list[str]:
        """Return candidate IDs ordered by relevance to the query."""
        raw_output = self.client.generate(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a strict academic retrieval reranker. "
                        "Rank only the provided candidate IDs by relevance to the query. "
                        "Return only JSON with this schema: "
                        '{"ranked_ids":["R1","R2"]}. Do not add commentary.'
                    ),
                },
                {
                    "role": "user",
                    "content": _build_rank_prompt(query, candidates),
                },
            ],
            temperature=self.model_config.get("temperature", 0),
            max_tokens=self.model_config.get("max_tokens", 512),
        )
        ranked_ids = _parse_ranked_ids(raw_output)
        valid_ids = {candidate["id"] for candidate in candidates}
        return [candidate_id for candidate_id in ranked_ids if candidate_id in valid_ids]

    def score(self, query: str, documents: list[str]) -> list[float]:
        """Compatibility shim for callers that need scores.

        Chat reranking is order-based, so this maps the returned order to
        descending synthetic scores.
        """
        candidates = [
            {"id": f"R{index}", "document": document}
            for index, document in enumerate(documents, start=1)
        ]
        ranked_ids = self.rank(query, candidates)
        score_by_id = {
            candidate_id: float(len(ranked_ids) - index)
            for index, candidate_id in enumerate(ranked_ids)
        }
        return [score_by_id.get(candidate["id"], 0.0) for candidate in candidates]


def _build_rank_prompt(query: str, candidates: list[dict[str, str]]) -> str:
    """Build the model prompt for one reranking request."""
    rendered = []
    for candidate in candidates:
        title = candidate.get("title", "")
        year = candidate.get("year", "")
        abstract = candidate.get("abstract", "")
        rendered.append(
            f"[{candidate['id']}]\n"
            f"Title: {title}\n"
            f"Year: {year}\n"
            f"Abstract: {abstract}"
        )
    return (
        f"Query:\n{query}\n\n"
        "Candidates:\n"
        f"{chr(10).join(rendered)}\n\n"
        "Return all relevant candidate IDs in descending relevance order. "
        "Use only IDs present above."
    )


def _parse_ranked_ids(raw_output: str) -> list[str]:
    """Parse ranked IDs from a JSON object, including fenced JSON."""
    text = raw_output.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    data: Any = json.loads(text)
    ranked_ids = data.get("ranked_ids") if isinstance(data, dict) else None
    if not isinstance(ranked_ids, list):
        raise ValueError("Reranker output must contain a ranked_ids list.")
    return [str(item) for item in ranked_ids]

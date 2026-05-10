"""Purpose: Generate search tags and queries from dimension-specific questions."""

from __future__ import annotations


def generate_queries(question: str, max_queries: int = 4) -> list[str]:
    """Scaffold query generation; future implementation will use an LLM."""
    return [question][:max_queries]


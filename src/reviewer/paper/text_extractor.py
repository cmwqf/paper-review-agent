"""Purpose: Extract paper text from PDF or text files for LLM context."""

from __future__ import annotations

from pathlib import Path


def extract_text(path: str | Path, max_chars: int | None = None) -> str:
    """Extract text; scaffold supports plain text files only."""
    text = Path(path).read_text(encoding="utf-8")
    return text[:max_chars] if max_chars else text


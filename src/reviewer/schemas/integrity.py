"""Purpose: Schema for one reference's citation-existence verification result."""

from __future__ import annotations

from pydantic import BaseModel


class CitationFinding(BaseModel):
    """Verification outcome for one bibliography entry."""

    index: str = ""
    title: str = ""
    arxiv_id: str | None = None
    doi: str | None = None
    # exists: confirmed real | nonexistent: confirmed fabricated | unverifiable: unknown
    status: str = "unverifiable"
    confidence: str = "medium"  # low | medium | high
    matched_title: str | None = None
    match_score: float | None = None
    evidence: str = ""

"""Purpose: Schema for the aggregated final review."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FinalReview(BaseModel):
    """Final review synthesized from all dimension reviews."""

    final_score: float = Field(ge=1.0, le=10.0)
    summary: str
    strengths: list[str] = []
    weaknesses: list[str] = []
    requested_changes: list[str] = []
    confidence: str


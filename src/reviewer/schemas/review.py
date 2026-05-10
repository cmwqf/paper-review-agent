"""Purpose: Schema for one dimension review produced after a Q&A trajectory."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DimensionReview(BaseModel):
    """Contribution, Soundness, or Presentation review."""

    dimension: str
    score: float = Field(ge=1.0, le=10.0)
    strengths: list[str] = []
    weaknesses: list[str] = []
    evidence_summary: str | None = None
    rationale: str


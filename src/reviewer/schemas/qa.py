"""Purpose: Schema for Q&A answers and their review impact metadata."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewImpact(BaseModel):
    """How a Q&A answer affects a dimension review."""

    dimension: str
    polarity: str
    severity: str
    score_impact: float = Field(ge=-2.0, le=2.0)
    confidence: str
    rationale: str


class QAResult(BaseModel):
    """Structured result returned by QATool.ask."""

    question: str
    answer: str
    evidence: list[str] = []
    retrieved_papers: list[dict] = []
    review_impact: ReviewImpact


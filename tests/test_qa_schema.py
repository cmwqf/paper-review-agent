"""Purpose: Tests for Q&A result schema and review-impact constraints."""

import pytest
from pydantic import ValidationError

from reviewer.schemas.qa import QAResult, ReviewImpact


def test_qa_result_requires_bounded_score_impact() -> None:
    """Ensure score impact stays in the configured conceptual range."""
    with pytest.raises(ValidationError):
        QAResult(
            question="Are baselines sufficient?",
            answer="No.",
            review_impact=ReviewImpact(
                dimension="Soundness",
                polarity="weakness",
                severity="major",
                score_impact=-3.0,
                confidence="high",
                rationale="Impact is intentionally out of bounds.",
            ),
        )


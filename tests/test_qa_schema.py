"""Purpose: Tests for Q&A result schema and review-impact constraints."""

from reviewer.schemas.qa import QAResult, ReviewImpact


def test_qa_result_accepts_simplified_review_impact() -> None:
    """QAResult should carry the simplified discrete impact labels."""
    result = QAResult(
        question="Are baselines sufficient?",
        answer="No. The answer explains why the issue matters.",
        review_impact=ReviewImpact(
            dimension="Soundness",
            polarity="weakness",
            impact_level="C2",
            confidence="high",
        ),
    )

    assert result.review_impact.impact_level == "C2"

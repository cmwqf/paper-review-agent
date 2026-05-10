"""Purpose: Final Review Agent output schema."""

from __future__ import annotations

from reviewer.schemas.final_review import FinalReview


class AggregatedFinalReview(FinalReview):
    """Final review schema specialized for aggregation output."""


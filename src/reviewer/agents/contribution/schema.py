"""Purpose: Contribution-specific schema aliases or extensions."""

from __future__ import annotations

from reviewer.schemas.review import DimensionReview


class ContributionReview(DimensionReview):
    """Review schema specialized for Contribution."""


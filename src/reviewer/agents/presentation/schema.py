"""Purpose: Presentation-specific schema aliases or extensions."""

from __future__ import annotations

from reviewer.schemas.review import DimensionReview


class PresentationReview(DimensionReview):
    """Review schema specialized for Presentation."""


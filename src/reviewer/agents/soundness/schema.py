"""Purpose: Soundness-specific schema aliases or extensions."""

from __future__ import annotations

from reviewer.schemas.review import DimensionReview


class SoundnessReview(DimensionReview):
    """Review schema specialized for Soundness."""


"""Purpose: Summary Agent output schema aliases."""

from __future__ import annotations

from reviewer.schemas.summary import SummarySchema


class PaperSummary(SummarySchema):
    """Summary Agent paper-map output parsed from XML."""

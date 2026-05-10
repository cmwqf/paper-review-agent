"""Purpose: Contribution Agent logic for novelty and impact review."""

from __future__ import annotations

from reviewer.agents.dimension_base import DimensionAgent
from reviewer.dimensions import ReviewDimension


class ContributionAgent(DimensionAgent):
    """Evaluate novelty, positioning, and potential impact."""

    name = "contribution"
    dimension = ReviewDimension.CONTRIBUTION


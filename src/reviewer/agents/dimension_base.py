"""Purpose: Shared Q&A trajectory state machine for dimension agents."""

from __future__ import annotations

from reviewer.agents.base import BaseAgent
from reviewer.dimensions import ReviewDimension


class DimensionAgent(BaseAgent):
    """Base class for Contribution, Soundness, and Presentation agents."""

    dimension: ReviewDimension

    def run(self, paper: dict, summary_xml: str) -> str:
        """Run Q&A turns until the agent writes a dimension review XML."""
        raise NotImplementedError("DimensionAgent.run is scaffolded.")


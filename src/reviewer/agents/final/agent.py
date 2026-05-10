"""Purpose: Aggregate dimension reviews into the final review XML."""

from __future__ import annotations

from reviewer.agents.base import BaseAgent


class FinalReviewAgent(BaseAgent):
    """Synthesize Contribution, Soundness, and Presentation reviews."""

    name = "final"

    def run(self, summary_xml: str, dimension_reviews: dict[str, str]) -> str:
        """Return `<final_review>` XML for the paper."""
        raise NotImplementedError("FinalReviewAgent.run is scaffolded.")


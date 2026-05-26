"""Purpose: Aggregate dimension reviews into the final review XML."""

from __future__ import annotations

from reviewer.agents.base import BaseAgent
from reviewer.models.factory import build_llm
from reviewer.tools.xml_validator import validate_xml_root
from reviewer.utils.prompts import load_prompt


class FinalReviewAgent(BaseAgent):
    """Synthesize Contribution, Soundness, and Presentation reviews."""

    name = "final"

    def run(self, summary_xml: str, dimension_reviews: dict[str, str]) -> str:
        """Return `<final_review>` XML for the paper."""
        model_key = self.config.get("agents", {}).get("final", {}).get("model", "final_review")
        client = build_llm(self.config, model_key)
        prompt = load_prompt("prompts/final_review_xml.md", config=self.config)
        raw_output = client.generate(
            [
                {
                    "role": "system",
                    "content": (
                        "You are the Final Review Agent. Synthesize the dimension "
                        "reviews into one final score and an Accept or Reject recommendation.\n\n"
                        f"{prompt}"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Paper summary XML:\n{summary_xml}\n\n"
                        "Dimension review XML documents:\n"
                        f"{_render_dimension_reviews(dimension_reviews)}"
                    ),
                },
            ]
        )
        self.trace_events = [
            {
                "agent": self.name,
                "event": "model_output",
                "raw_output": raw_output,
            }
        ]
        return validate_xml_root(raw_output, "final_review")


def _render_dimension_reviews(dimension_reviews: dict[str, str]) -> str:
    """Render dimension reviews in a stable order."""
    order = ["Contribution", "Soundness", "Presentation"]
    parts = []
    for key in order:
        if key in dimension_reviews:
            parts.append(f"## {key}\n{dimension_reviews[key]}")
    for key, value in dimension_reviews.items():
        if key not in order:
            parts.append(f"## {key}\n{value}")
    return "\n\n".join(parts)

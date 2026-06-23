"""Purpose: Aggregate dimension reviews into the final review XML."""

from __future__ import annotations

from reviewer.agents.base import BaseAgent
from reviewer.models.factory import build_llm
from reviewer.utils.prompts import load_prompt, load_rubric_prompt
from reviewer.utils.xml_retry import generate_valid_xml


class FinalReviewAgent(BaseAgent):
    """Synthesize Contribution, Soundness, and Presentation reviews."""

    name = "final"

    def run(
        self,
        summary_xml: str,
        dimension_reviews: dict[str, str],
        qa_trajectories: dict[str, list] | None = None,
    ) -> str:
        """Return `<final_review>` XML for the paper.

        ``qa_trajectories`` is accepted for call-site compatibility but no longer
        fed to the model: the raw Q&A bank is redundant with each dimension
        review's own ``<evidence_trace>`` (which carries the supporting Q&A ids),
        so the final stage aggregates the three dimension reviews directly.
        """
        model_key = self.config.get("agents", {}).get("final", {}).get("model", "final_review")
        client = build_llm(self.config, model_key)
        prompt = load_prompt("prompts/final_review_xml.md", config=self.config)
        rubric_prompt = load_rubric_prompt(self.config)
        self.trace_events = []
        max_attempts = int(self.config.get("xml", {}).get("max_generation_attempts", 5))
        return generate_valid_xml(
            client=client,
            root_tag="final_review",
            max_attempts=max_attempts,
            trace_events=self.trace_events,
            trace_base={"agent": self.name},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the Final Review Agent. Synthesize the dimension "
                        "reviews into one final score and an Accept or Reject recommendation.\n\n"
                        f"{rubric_prompt}\n\n"
                        f"{prompt}"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Paper summary XML:\n{summary_xml}\n\n"
                        "Dimension review XML documents (your primary inputs; each "
                        "already carries its own <evidence_trace> with the supporting "
                        "Q&A ids, plus <decisive_issues> and <key_points>):\n"
                        f"{_render_dimension_reviews(dimension_reviews)}"
                    ),
                },
            ],
        )


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

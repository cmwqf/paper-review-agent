"""Purpose: Generate the structured XML summary consumed by all dimension agents."""

from __future__ import annotations

from reviewer.agents.base import BaseAgent
from reviewer.models.factory import build_llm
from reviewer.utils.prompts import load_prompt
from reviewer.utils.xml_retry import generate_valid_xml


class SummaryAgent(BaseAgent):
    """Create a paper summary in XML format."""

    name = "summary"

    def run(self, paper: dict) -> str:
        """Return `<paper_summary>` XML for the input paper."""
        model_key = self.config.get("agents", {}).get("summary", {}).get("model", "summary")
        client = build_llm(self.config, model_key)
        system_prompt = load_prompt("prompts/summary_agent_system.md", config=self.config)
        output_prompt = load_prompt("prompts/summary_agent_output_contract.md", config=self.config)

        max_chars = int(self.config.get("paper", {}).get("max_text_chars", 120000))
        paper_text = str(paper.get("text") or "")[:max_chars]
        metadata = paper.get("metadata", {})

        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n{output_prompt}"},
            {
                "role": "user",
                "content": (
                    "Generate a structured XML summary for the following paper.\n\n"
                    f"Paper metadata:\n{metadata}\n\n"
                    f"Paper text:\n{paper_text}"
                ),
            },
        ]
        # Retry on malformed XML (e.g. an unescaped '<' from a math inequality),
        # mirroring the dimension agents instead of crashing the whole paper.
        max_attempts = int(self.config.get("xml", {}).get("max_generation_attempts", 5))
        self.trace_events = []
        return generate_valid_xml(
            client=client,
            messages=messages,
            root_tag="paper_summary",
            max_attempts=max_attempts,
            trace_events=self.trace_events,
            trace_base={"agent": self.name},
        )

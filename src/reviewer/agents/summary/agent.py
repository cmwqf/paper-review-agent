"""Purpose: Generate the structured XML summary consumed by all dimension agents."""

from __future__ import annotations

from reviewer.agents.base import BaseAgent
from reviewer.models.factory import build_llm
from reviewer.tools.xml_validator import validate_xml_root
from reviewer.utils.prompts import load_prompt


class SummaryAgent(BaseAgent):
    """Create a paper summary in XML format."""

    name = "summary"

    def run(self, paper: dict) -> str:
        """Return `<paper_summary>` XML for the input paper."""
        model_key = self.config.get("agents", {}).get("summary", {}).get("model", "summary")
        client = build_llm(self.config, model_key)
        system_prompt = load_prompt("prompts/summary_system.md", config=self.config)
        output_prompt = load_prompt("prompts/summary_output_xml.md", config=self.config)

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
        raw_output = client.generate(messages)
        self.trace_events = [
            {
                "agent": self.name,
                "event": "model_output",
                "raw_output": raw_output,
            }
        ]
        return validate_xml_root(raw_output, "paper_summary")

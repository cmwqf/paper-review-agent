"""Purpose: Shared Q&A trajectory state machine for dimension agents."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from reviewer.agents.answer.agent import AnswerAgent
from reviewer.agents.base import BaseAgent
from reviewer.dimensions import ReviewDimension
from reviewer.models.factory import build_llm
from reviewer.schemas.qa import QAResult
from reviewer.schemas.summary import parse_summary_xml, render_summary_for_agent
from reviewer.tools.xml_validator import extract_xml_document, validate_xml_root
from reviewer.utils.prompts import load_prompt


class DimensionAgent(BaseAgent):
    """Base class for Contribution, Soundness, and Presentation agents."""

    dimension: ReviewDimension

    def run(self, paper: dict, summary_xml: str) -> str:
        """Run Q&A turns and return only the dimension review XML."""
        review_xml, _ = self.run_with_qa(paper, summary_xml)
        return review_xml

    def run_with_qa(self, paper: dict, summary_xml: str) -> tuple[str, list[QAResult]]:
        """Run Q&A turns until the agent writes a dimension review XML."""
        model_key = self.config.get("agents", {}).get(self.name, {}).get("model", "agent")
        client = build_llm(self.config, model_key)
        summary = parse_summary_xml(summary_xml)
        paper_map = render_summary_for_agent(summary)
        qa_results = self.initial_qa_results(paper, summary_xml)
        max_turns = int(self.config.get("agents", {}).get(self.name, {}).get("max_qa_turns", 5))
        min_turns = int(self.config.get("agents", {}).get(self.name, {}).get("min_qa_turns", 0))
        require_balanced_qa = bool(
            self.config.get("agents", {}).get(self.name, {}).get("require_balanced_qa", True)
        )
        system_prompt = _dimension_system_prompt(self.config, self.name)
        feedback = ""
        self.trace_events = []

        for turn_index in range(max_turns + 1):
            raw_output = client.generate(
                [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": _dimension_context(
                            dimension=self.dimension.value,
                            paper=paper,
                            paper_map=paper_map,
                            qa_results=qa_results,
                            turn_index=turn_index,
                            max_turns=max_turns,
                            min_turns=min_turns,
                            require_balanced_qa=require_balanced_qa,
                            feedback=feedback,
                        ),
                    },
                ]
            )
            self.trace_events.append(
                {
                    "agent": self.name,
                    "event": "model_output",
                    "turn": turn_index,
                    "dimension": self.dimension.value,
                    "raw_output": raw_output,
                }
            )
            review_xml = extract_xml_document(raw_output, "dimension_review")
            if review_xml != raw_output.strip() or raw_output.strip().startswith("<dimension_review"):
                missing_feedback = _missing_qa_feedback(qa_results, min_turns, require_balanced_qa)
                if missing_feedback and turn_index < max_turns:
                    feedback = missing_feedback
                    continue
                return validate_xml_root(review_xml, "dimension_review"), qa_results

            action = _parse_dimension_action(raw_output)
            missing_feedback = _missing_qa_feedback(qa_results, min_turns, require_balanced_qa)
            if action["action"] == "write_review" and missing_feedback and turn_index < max_turns:
                feedback = missing_feedback
                continue
            if action["action"] == "write_review" or turn_index >= max_turns:
                review_xml = _write_dimension_review(
                    client=client,
                    config=self.config,
                    dimension=self.dimension.value,
                    paper_map=paper_map,
                    qa_results=qa_results,
                )
                return review_xml, qa_results
            if action["action"] != "ask_question":
                raise ValueError(f"Unsupported dimension action: {action['action']}")
            question = action["question"]
            if not question:
                if missing_feedback and turn_index < max_turns:
                    feedback = f"You returned an empty question. {missing_feedback}"
                    continue
                review_xml = _write_dimension_review(
                    client=client,
                    config=self.config,
                    dimension=self.dimension.value,
                    paper_map=paper_map,
                    qa_results=qa_results,
                )
                return review_xml, qa_results
            self.trace_events.append(
                {
                    "agent": self.name,
                    "event": "ask_question",
                    "turn": turn_index,
                    "dimension": self.dimension.value,
                    "question": question,
                    "rationale": action["rationale"],
                }
            )
            qa_results.append(
                AnswerAgent(self.config).run(
                    question,
                    self.dimension.value,
                    paper,
                    summary,
                    prior_qa_results=qa_results,
                )
            )
            feedback = ""

        review_xml = _write_dimension_review(
            client=client,
            config=self.config,
            dimension=self.dimension.value,
            paper_map=paper_map,
            qa_results=qa_results,
        )
        return review_xml, qa_results

    def initial_qa_results(self, paper: dict, summary_xml: str) -> list[QAResult]:
        """Return dimension-specific preloaded evidence before model-directed Q&A."""
        _ = (paper, summary_xml)
        return []


def _dimension_system_prompt(config: dict, agent_name: str) -> str:
    """Build the dimension agent system prompt with the action/review XML contracts."""
    prompt_path = f"prompts/{agent_name}_agent.md"
    prompt = load_prompt(prompt_path, config=config)
    review_contract = load_prompt("prompts/dimension_review_xml.md", config=config)
    agent_config = config.get("agents", {}).get(agent_name, {})
    min_turns = int(agent_config.get("min_qa_turns", 0))
    max_turns = int(agent_config.get("max_qa_turns", 5))
    require_balanced_qa = bool(agent_config.get("require_balanced_qa", True))
    balanced_rule = (
        "You must also collect at least one Q&A result whose review_impact "
        "polarity is `strength` and at least one whose polarity is `weakness` "
        "before writing the review."
        if require_balanced_qa
        else "Balanced strength/weakness Q&A coverage is not required for this run."
    )
    action_contract = f"""
For intermediate turns, return exactly one `<dimension_action>` XML document:

<dimension_action>
  <action>ask_question | write_review</action>
  <question>Focused question for the Answer Agent. Leave empty for write_review.</question>
  <rationale>Why this question is needed, or why the review is ready.</rationale>
</dimension_action>

Ask at most one question per turn. You must collect at least {min_turns} Q&A
result(s) before writing the review, and you may ask up to {max_turns} question(s).
{balanced_rule}
Do not return `write_review` or `<dimension_review>` before the Q&A trajectory
contains at least {min_turns} result(s) and satisfies the required polarity
coverage. After the minimum and polarity coverage are reached, prefer writing
the review once the remaining uncertainty is unlikely to change the dimension
score.
"""
    return f"{prompt}\n\n{action_contract}\n\n{review_contract}"


def _dimension_context(
    *,
    dimension: str,
    paper: dict,
    paper_map: str,
    qa_results: list[QAResult],
    turn_index: int,
    max_turns: int,
    min_turns: int,
    require_balanced_qa: bool,
    feedback: str = "",
) -> str:
    """Render dimension-agent state for the next decision."""
    qa_text = "\n\n".join(_render_qa_result(result, index) for index, result in enumerate(qa_results, 1))
    if not qa_text:
        qa_text = "No Q&A results yet."
    return (
        f"Dimension: {dimension}\n"
        f"Turn: {turn_index} of {max_turns}\n"
        f"Minimum Q&A results before review: {min_turns}\n"
        f"Require at least one strength and one weakness Q&A before review: {require_balanced_qa}\n"
        f"Current Q&A polarity coverage: {_qa_polarity_coverage(qa_results)}\n"
        f"Current Q&A results: {len(qa_results)}\n"
        f"{'Feedback: ' + feedback + chr(10) if feedback else ''}"
        f"Paper metadata:\n{paper.get('metadata', {})}\n\n"
        f"Paper map:\n{paper_map}\n\n"
        f"Q&A trajectory:\n{qa_text}\n"
    )


def _qa_polarity_coverage(qa_results: list[QAResult]) -> str:
    """Return a compact summary of strength/weakness evidence coverage."""
    polarities = {
        str(result.review_impact.polarity).strip().lower()
        for result in qa_results
        if getattr(result, "review_impact", None) is not None
    }
    has_strength = "strength" in polarities
    has_weakness = "weakness" in polarities
    return f"strength={has_strength}, weakness={has_weakness}"


def _missing_qa_feedback(
    qa_results: list[QAResult],
    min_turns: int,
    require_balanced_qa: bool,
) -> str:
    """Explain what Q&A coverage is still required before writing a review."""
    missing = []
    if len(qa_results) < min_turns:
        missing.append(
            f"this dimension requires at least {min_turns} Q&A results, "
            f"but currently has {len(qa_results)}"
        )
    if require_balanced_qa:
        polarities = {
            str(result.review_impact.polarity).strip().lower()
            for result in qa_results
            if getattr(result, "review_impact", None) is not None
        }
        if "strength" not in polarities:
            missing.append("ask a question that can identify a strength")
        if "weakness" not in polarities:
            missing.append("ask a question that can identify a weakness")
    if not missing:
        return ""
    return "You cannot write the review yet: " + "; ".join(missing) + "."


def _render_qa_result(result: QAResult, index: int) -> str:
    """Render one QAResult for dimension review decisions."""
    impact = result.review_impact
    refs = "; ".join(result.evidence[:6])
    return (
        f"Q{index}: {result.question}\n"
        f"Answer: {result.answer}\n"
        f"Impact: {impact.polarity}, {impact.impact_level}, confidence={impact.confidence}\n"
        f"Refs: {refs or 'none'}"
    )


def _parse_dimension_action(raw_output: str) -> dict[str, str]:
    """Parse `<dimension_action>` XML."""
    action_xml = validate_xml_root(raw_output, "dimension_action")
    root = ET.fromstring(action_xml)
    return {
        "action": _child_text(root, "action"),
        "question": _child_text(root, "question"),
        "rationale": _child_text(root, "rationale"),
    }


def _write_dimension_review(
    *,
    client,
    config: dict,
    dimension: str,
    paper_map: str,
    qa_results: list[QAResult],
) -> str:
    """Ask the dimension model to write the final dimension review XML."""
    review_contract = load_prompt("prompts/dimension_review_xml.md", config=config)
    qa_text = "\n\n".join(_render_qa_result(result, index) for index, result in enumerate(qa_results, 1))
    raw_output = client.generate(
        [
            {
                "role": "system",
                "content": (
                    f"Write the final {dimension} dimension review now. "
                    "Use only the paper map and Q&A trajectory.\n\n"
                    f"{review_contract}"
                ),
            },
            {
                "role": "user",
                "content": f"Paper map:\n{paper_map}\n\nQ&A trajectory:\n{qa_text or 'No Q&A results.'}",
            },
        ]
    )
    return validate_xml_root(raw_output, "dimension_review")


def _child_text(root: ET.Element, name: str) -> str:
    """Read child text from an XML element."""
    child = root.find(name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()

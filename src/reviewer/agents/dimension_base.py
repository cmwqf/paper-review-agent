"""Purpose: Shared Q&A trajectory state machine for dimension agents."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Callable

from reviewer.agents.answer.agent import AnswerAgent
from reviewer.agents.base import BaseAgent
from reviewer.dimensions import ReviewDimension
from reviewer.models.factory import build_llm
from reviewer.schemas.qa import QAResult
from reviewer.schemas.summary import parse_summary_xml, render_summary_for_agent
from reviewer.tools.xml_validator import extract_xml_document, validate_xml_root
from reviewer.utils.prompts import load_prompt, load_rubric_prompt
from reviewer.utils.xml_retry import generate_valid_xml


class DimensionAgent(BaseAgent):
    """Base class for Contribution, Soundness, and Presentation agents."""

    dimension: ReviewDimension

    def run(self, paper: dict, summary_xml: str) -> str:
        """Run Q&A turns and return only the dimension review XML."""
        review_xml, _ = self.run_with_qa(paper, summary_xml)
        return review_xml

    def run_with_qa(
        self,
        paper: dict,
        summary_xml: str,
        preloaded_qa_results: list[QAResult] | None = None,
        on_qa_result: Callable[[QAResult], None] | None = None,
    ) -> tuple[str, list[QAResult]]:
        """Run Q&A turns until the agent ends questions and writes a review XML.

        ``preloaded_qa_results`` lets a crash-resume continue a partially
        answered dimension: the already-answered questions are seeded into the
        trajectory (counting against the per-dimension turn budget) so only the
        cheap question-selection loop replays and the expensive AnswerAgent runs
        are not redone. ``on_qa_result`` is invoked once per *freshly* answered
        question (never for the preloaded ones), letting the caller checkpoint
        each answer to durable storage as it lands.
        """
        model_key = self.config.get("agents", {}).get(self.name, {}).get("model", "agent")
        client = build_llm(self.config, model_key)
        summary = parse_summary_xml(summary_xml)
        paper_map = render_summary_for_agent(summary)
        # Deterministic preloaded evidence (e.g. Presentation compliance gates) is
        # regenerated every run and is not a question turn; resumed model answers
        # are appended after it and DO count against the turn budget below.
        qa_results = self.initial_qa_results(paper, summary_xml)
        preloaded_turns = len(preloaded_qa_results) if preloaded_qa_results else 0
        if preloaded_qa_results:
            qa_results.extend(preloaded_qa_results)
        max_turns = int(self.config.get("agents", {}).get(self.name, {}).get("max_qa_turns", 5))
        min_turns = int(self.config.get("agents", {}).get(self.name, {}).get("min_qa_turns", 0))
        require_balanced_qa = bool(
            self.config.get("agents", {}).get(self.name, {}).get("require_balanced_qa", True)
        )
        # Put the stable per-paper context (metadata, paper map, calibration) in
        # the system prompt so it stays byte-identical across this dimension's
        # turns and Claude Code's prompt cache (anchored at the system prompt) is
        # reused instead of recreated on every call.
        system_prompt = _dimension_cached_system(
            self.config, self.name, self.dimension.value, paper, paper_map
        )
        feedback = ""
        max_format_retries = int(self.config.get("qa", {}).get("max_format_retries", 3))
        self.trace_events = []

        for turn_index in range(preloaded_turns, max_turns + 1):
            base_messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": _dimension_context(
                        dimension=self.dimension.value,
                        qa_results=qa_results,
                        turn_index=turn_index,
                        max_turns=max_turns,
                        min_turns=min_turns,
                        require_balanced_qa=require_balanced_qa,
                        feedback=feedback,
                    ),
                },
            ]
            raw_output = client.generate(base_messages)
            self.trace_events.append(
                {
                    "agent": self.name,
                    "event": "model_output",
                    "turn": turn_index,
                    "dimension": self.dimension.value,
                    "raw_output": raw_output,
                }
            )
            try:
                action = _parse_dimension_tool_call(
                    raw_output,
                    client=client,
                    base_messages=base_messages,
                    max_retries=max_format_retries,
                    trace_events=self.trace_events,
                )
            except (ET.ParseError, ValueError):
                # Persistent malformed <action> XML (e.g. an unescaped
                # '<' in an inequality). Don't lose the whole paper: write the
                # review from the Q&A gathered so far.
                review_xml = _write_dimension_review(
                    client=client,
                    config=self.config,
                    dimension=self.dimension.value,
                    paper_map=paper_map,
                    qa_results=qa_results,
                )
                return review_xml, qa_results
            missing_feedback = _missing_qa_feedback(qa_results, min_turns, require_balanced_qa)
            self.trace_events.append(
                {
                    "agent": self.name,
                    "event": "tool_call",
                    "turn": turn_index,
                    "dimension": self.dimension.value,
                    "action": action,
                }
            )
            if action["action"] == "end_questions" and missing_feedback and turn_index < max_turns:
                feedback = missing_feedback
                continue
            if action["action"] == "end_questions" or turn_index >= max_turns:
                review_xml = _write_dimension_review(
                    client=client,
                    config=self.config,
                    dimension=self.dimension.value,
                    paper_map=paper_map,
                    qa_results=qa_results,
                )
                return review_xml, qa_results
            if action["action"] != "ask_question":
                raise ValueError(f"Unsupported dimension tool: {action['action']}")
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
            answer_result = AnswerAgent(self.config).run(
                question,
                self.dimension.value,
                paper,
                summary,
                prior_qa_results=qa_results,
            )
            qa_results.append(answer_result)
            if on_qa_result is not None:
                # Checkpoint this freshly answered question immediately so a hard
                # process kill mid-dimension does not discard the expensive run.
                on_qa_result(answer_result)
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
    """Build the dimension agent system prompt with the question tool-call contract."""
    prompt_path = f"prompts/{agent_name}_question_agent_guidance.md"
    prompt = load_prompt(prompt_path, config=config)
    rubric_prompt = load_rubric_prompt(config)
    agent_config = config.get("agents", {}).get(agent_name, {})
    min_turns = int(agent_config.get("min_qa_turns", 0))
    max_turns = int(agent_config.get("max_qa_turns", 5))
    require_balanced_qa = bool(agent_config.get("require_balanced_qa", True))
    balanced_rule = (
        "You must also collect at least one Q&A result whose review_impact "
        "polarity is `strength` and at least one whose polarity is `weakness` "
        "before ending questions."
        if require_balanced_qa
        else (
            "Balanced strength/weakness coverage is not mechanically enforced, but "
            "make sure at least one question captures the paper's main strength so "
            "the review is not skewed toward reject. You do not need to confirm "
            "strengths exhaustively. Spend the rest of the questions digging for "
            "distinct weaknesses until they are exhausted."
        )
    )
    action_contract = f"""
QUESTION TOOL-CALL STAGE

Every response in this stage must be exactly one `<action>` XML document and
nothing else. Do not output `<dimension_action>`, `<dimension_review>`, markdown
fences, explanatory text, or multiple XML documents. If you emit more than one
`<action>`, only the FIRST is executed and the rest are ignored, so never
batch actions.

Choose exactly one tool per turn. Use `ask_question` to ask the Answer Agent one
focused evidence question. Use `end_questions` when Q&A evidence is saturated;
after a valid `end_questions`, the runtime exits this question stage and invokes
the separate dimension-review writer.

For `ask_question`:
<action>
  <tool_name>ask_question</tool_name>
  <question>Focused question for the Answer Agent.</question>
  <rationale>Why this question is needed.</rationale>
</action>

For `end_questions`, include only `tool_name` and `rationale`:
<action>
  <tool_name>end_questions</tool_name>
  <rationale>Why question gathering is complete.</rationale>
</action>

Ask at most one question per turn. You must collect at least {min_turns} Q&A
result(s) before ending questions, and you may ask up to {max_turns} question(s).
{balanced_rule}
Do not use `end_questions` or output `<dimension_review>` before the Q&A trajectory
contains at least {min_turns} result(s).

Decide when to stop by saturation, not by the minimum. After the minimum is
reached, do NOT end questions just because you hit the minimum. Keep asking
while a new question is likely to surface a NEW, distinct weakness you have not
yet examined (or to capture the main strength if you have not). End questions
only when both: (a) your most recent question(s) stopped surfacing new
score-relevant weaknesses, so the main weaknesses a careful human reviewer would
raise are exhausted; and (b) the paper's main strength is captured. Use as many
of the up-to-{max_turns} questions as the paper's distinct weaknesses warrant;
papers with many real issues should use more questions than papers with few.
"""
    return f"{rubric_prompt}\n\n{prompt}\n\n{action_contract}"


def _dimension_paper_context(dimension: str, paper: dict, paper_map: str) -> str:
    """Stable per-paper context (metadata, paper map, calibration guidance).

    Kept identical across a dimension's turns so it can live in the cached
    system prompt rather than being re-sent (and re-billed) every turn.
    """
    return (
        f"Dimension-specific calibration guidance:\n{_dimension_calibration_guidance(dimension)}\n\n"
        f"Paper metadata:\n{paper.get('metadata', {})}\n\n"
        f"Paper map:\n{paper_map}"
    )


def _dimension_cached_system(
    config: dict, agent_name: str, dimension: str, paper: dict, paper_map: str
) -> str:
    """Build the cache-anchored system prompt: instructions + stable paper context."""
    return (
        f"{_dimension_system_prompt(config, agent_name)}\n\n"
        f"{_dimension_paper_context(dimension, paper, paper_map)}"
    )


def _dimension_context(
    *,
    dimension: str,
    qa_results: list[QAResult],
    turn_index: int,
    max_turns: int,
    min_turns: int,
    require_balanced_qa: bool,
    feedback: str = "",
) -> str:
    """Render the turn-varying dimension-agent state for the next decision.

    The stable paper context is supplied separately via the system prompt (see
    :func:`_dimension_cached_system`); only the per-turn state lives here.
    """
    qa_text = _render_qa_for_dimension_review(dimension, qa_results)
    return (
        f"Dimension: {dimension}\n"
        f"Turn: {turn_index} of {max_turns}\n"
        f"Minimum Q&A results before review: {min_turns}\n"
        f"Require at least one strength and one weakness Q&A before review: {require_balanced_qa}\n"
        f"Current Q&A polarity coverage: {_qa_polarity_coverage(qa_results)}\n"
        f"Current Q&A results: {len(qa_results)}\n"
        f"Stop decision: if a distinct, score-relevant weakness area still looks "
        f"unexamined, ask one more question about it. Only end questions once "
        f"your recent questions stopped finding new weaknesses (the main weaknesses "
        f"are exhausted) and the paper's main strength is captured. Do not stop just "
        f"because the minimum is reached.\n"
        f"{'Feedback: ' + feedback + chr(10) if feedback else ''}"
        f"Q&A evidence for this dimension:\n{qa_text}\n"
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
    return "You cannot end questions yet: " + "; ".join(missing) + "."


def _render_qa_result(result: QAResult, index: int) -> str:
    """Render one QAResult for dimension review decisions."""
    impact = result.review_impact
    refs = "; ".join(result.evidence[:6])
    evidence_id = getattr(result, "id", None) or _qa_id(impact.dimension, index)
    return (
        f"{evidence_id}: {result.question}\n"
        f"Answer: {result.answer}\n"
        f"Impact: {impact.polarity}, {impact.impact_level}, confidence={impact.confidence}\n"
        f"Refs: {refs or 'none'}"
    )


def _render_qa_for_dimension_review(dimension: str, qa_results: list[QAResult]) -> str:
    """Render Q&A as one complete decision-oriented evidence ledger."""
    if not qa_results:
        return "No Q&A results yet."
    return _render_qa_evidence_ledger(dimension, qa_results)


def _render_qa_evidence_ledger(dimension: str, qa_results: list[QAResult]) -> str:
    """Group Q&A results by review impact so score-driving evidence is salient."""
    indexed = list(enumerate(qa_results, 1))
    grouped: dict[tuple[str, str], list[tuple[int, QAResult]]] = {}
    for index, result in indexed:
        impact = result.review_impact
        key = (
            str(impact.impact_level or "C4").strip().upper(),
            str(impact.polarity or "weakness").strip().lower(),
        )
        grouped.setdefault(key, []).append((index, result))

    lines = [
        "Evidence ledger grouped by review impact.",
        "Use this ledger as the primary interface for selecting key_points and assigning the dimension score.",
        "Do not average groups by count; choose findings by decision impact.",
        "",
    ]
    for impact_level, polarity, title in _ledger_group_order():
        items = grouped.get((impact_level, polarity), [])
        if not items:
            continue
        lines.extend([f"## {title}", ""])
        for index, result in items:
            lines.extend(_render_qa_evidence_card(dimension, result, index))
            lines.append("")

    remaining = [
        (key, items)
        for key, items in grouped.items()
        if key not in {(level, polarity) for level, polarity, _ in _ledger_group_order()}
    ]
    for (impact_level, polarity), items in sorted(remaining):
        lines.extend([f"## Other {impact_level} {polarity} findings", ""])
        for index, result in items:
            lines.extend(_render_qa_evidence_card(dimension, result, index))
            lines.append("")
    return "\n".join(lines).rstrip()


def _ledger_group_order() -> list[tuple[str, str, str]]:
    return [
        ("C0", "weakness", "C0 weaknesses / hard gates"),
        ("C1", "weakness", "C1 weaknesses"),
        ("C1", "strength", "C1 strengths"),
        ("C2", "weakness", "C2 weaknesses"),
        ("C2", "strength", "C2 strengths"),
        ("C3", "weakness", "C3 local weaknesses"),
        ("C3", "strength", "C3 local strengths"),
        ("C4", "weakness", "C4 trace weaknesses or evidence limitations"),
        ("C4", "strength", "C4 trace strengths"),
    ]


def _render_qa_evidence_card(dimension: str, result: QAResult, index: int) -> list[str]:
    impact = result.review_impact
    evidence_id = getattr(result, "id", None) or _qa_id(impact.dimension or dimension, index)
    refs = result.evidence[:3]
    lines = [
        f"- id: {evidence_id}",
        (
            "  impact: "
            f"polarity={impact.polarity}; impact_level={impact.impact_level}; "
            f"confidence={impact.confidence}"
        ),
        f"  review_implication: {_review_implication(dimension, impact.polarity, impact.impact_level)}",
        "  question: |",
        *[f"    {line}" for line in _indented_block(result.question)],
        "  answer: |",
        *[f"    {line}" for line in _indented_block(result.answer)],
    ]
    if refs:
        lines.append("  evidence_refs:")
        lines.extend(f"    - {ref}" for ref in refs)
    return lines


def _indented_block(text: str) -> list[str]:
    """Return lines suitable for a YAML-style block in the prompt."""
    lines = str(text or "").splitlines()
    return lines or [""]


def _review_implication(dimension: str, polarity: str, impact_level: str) -> str:
    """Explain how one finding should affect dimension scoring."""
    polarity = str(polarity or "").strip().lower()
    impact_level = str(impact_level or "C4").strip().upper()
    dimension = str(dimension or "").strip()
    if impact_level == "C0" and polarity == "weakness":
        return "Potential hard gate or non-reviewability issue; evaluate under the active rubric before ordinary scoring."
    if impact_level == "C1" and polarity == "weakness":
        if dimension == "Soundness":
            return "Score-driving concern; lower Soundness in proportion to its effect on central claims, protocol validity, or validation."
        if dimension == "Contribution":
            return "Score-driving limitation; lower Contribution in proportion to its effect on new knowledge, impact, or generality."
        if dimension == "Presentation":
            return "Score-driving reviewability issue; lower Presentation in proportion to its effect on assessment or reproducibility."
        return "Score-driving concern; should affect the score unless clearly outweighed."
    if impact_level == "C1" and polarity == "strength":
        return "Score-driving strength; can raise the score when it materially improves the dimension judgment under the rubric."
    if impact_level == "C2" and polarity == "weakness":
        return "Important limitation; usually affects the score boundary and should appear in weaknesses if unresolved."
    if impact_level == "C2" and polarity == "strength":
        return "Important support; can justify not scoring lower but should not alone override C1 weaknesses."
    if impact_level == "C3":
        return "Local point; usually belongs in suggestions or secondary prose rather than driving the score."
    return "Trace or low-priority point; do not let it drive the score unless it confirms a real central paper issue."


def _qa_id(dimension: str, index: int) -> str:
    prefixes = {
        "Contribution": "CONTRIB",
        "Soundness": "SOUND",
        "Presentation": "PRES",
    }
    prefix = prefixes.get(dimension, dimension.upper().replace(" ", "_") or "QA")
    return f"{prefix}-{index:03d}"


def _parse_dimension_tool_call(
    raw_output: str,
    *,
    client=None,
    base_messages: list | None = None,
    max_retries: int = 0,
    trace_events: list | None = None,
) -> dict[str, str]:
    """Parse one question-stage `<action>`, reprompting on malformed XML.

    Per-turn action XML occasionally contains unescaped ``&``, ``<``, or ``>``
    (e.g. an inequality inside a question), which makes the parser raise
    ParseError. A single bad turn would otherwise abort the entire dimension
    (and the paper). When a client is supplied, regenerate the action up to
    ``max_retries`` times, instructing the model to escape literal XML
    characters; with no client it parses once (back-compatible).
    """
    current = raw_output
    for attempt in range(max(0, max_retries) + 1):
        try:
            action_xml = _validate_dimension_tool_call_xml(current)
            root = ET.fromstring(action_xml)
            tool_name = _child_text(root, "tool_name")
            question = _child_text(root, "question")
            rationale = _child_text(root, "rationale")
            if tool_name not in {"ask_question", "end_questions"}:
                raise ValueError(f"Unsupported dimension tool_name: {tool_name!r}")
            if not rationale:
                raise ValueError(f"{tool_name} requires a non-empty <rationale>.")
            if tool_name == "ask_question" and not question:
                raise ValueError("ask_question requires a non-empty <question>.")
            allowed_children = {"tool_name", "question", "rationale"}
            if tool_name == "end_questions":
                allowed_children = {"tool_name", "rationale"}
                if root.find("question") is not None:
                    raise ValueError("end_questions must not include <question>; only <rationale>.")
            extras = [child.tag for child in root if child.tag not in allowed_children]
            if extras:
                raise ValueError(f"{tool_name} received unsupported field(s): {', '.join(extras)}.")
            return {
                "action": tool_name,
                "question": question,
                "rationale": rationale,
            }
        except (ET.ParseError, ValueError) as exc:
            if client is None or base_messages is None or attempt >= max_retries:
                raise
            if trace_events is not None:
                trace_events.append(
                    {
                        "event": "stage_contract_violation",
                        "stage": "question_tool_call",
                        "attempt": attempt + 1,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            current = client.generate(
                [
                    *base_messages,
                    {"role": "assistant", "content": current},
                    {
                        "role": "user",
                        "content": (
                            "The previous output was not valid question-stage <action> XML.\n"
                            f"Parser error: {type(exc).__name__}: {exc}\n\n"
                            "Output exactly one <action> XML document and nothing else. "
                            "Use tool_name=ask_question or tool_name=end_questions. "
                            "For end_questions include only <tool_name> and <rationale>. "
                            "Do not output <dimension_action> or <dimension_review>. "
                            "Do not wrap it in markdown fences. Escape every literal &, "
                            "<, and > in text content as &amp;, &lt;, and &gt;."
                        ),
                    },
                ]
            )
    raise RuntimeError("dimension tool-call retry loop exited unexpectedly")


def _validate_dimension_tool_call_xml(raw_output: str) -> str:
    """Validate the question-stage tool call, tolerating extra/multiple calls.

    The model sometimes emits several <action> documents (or wraps one in
    prose). Since the loop executes one action per turn, we use the first call
    rather than rejecting and wasting a retry. A wrong-stage root (a dimension
    action/review where a tool call is expected) is still a hard error.
    """
    if raw_output.count("<action") == 0:
        raise ValueError("Expected a <action> document, found none.")
    for disallowed in ("dimension_action", "dimension_review"):
        if raw_output.count(f"<{disallowed}"):
            raise ValueError(
                f"Invalid state output: question tool-call stage must not contain <{disallowed}>."
            )
    extracted = extract_xml_document(raw_output, "action")
    return validate_xml_root(extracted, "action")


def _write_dimension_review(
    *,
    client,
    config: dict,
    dimension: str,
    paper_map: str,
    qa_results: list[QAResult],
) -> str:
    """Ask the dimension model to write the final dimension review XML."""
    review_guidance = _load_dimension_review_prompt(config, dimension)
    review_contract = load_prompt("prompts/dimension_review_output_contract.md", config=config)
    rubric_prompt = load_rubric_prompt(config)
    qa_text = _render_qa_for_dimension_review(dimension, qa_results)
    max_attempts = int(config.get("xml", {}).get("max_generation_attempts", 5))
    return generate_valid_xml(
        client=client,
        root_tag="dimension_review",
        max_attempts=max_attempts,
        validator=_validate_dimension_review_contract,
        messages=[
            {
                "role": "system",
                # Stable blocks (guidance, contract, calibration, paper map) lead
                # so they sit in the cache-anchored system prompt.
                "content": (
                    f"Write the final {dimension} dimension review now. "
                        "Use only the paper map and this dimension's Q&A evidence ledger.\n\n"
                        f"{rubric_prompt}\n\n"
                        f"{review_guidance}\n\n"
                        f"{review_contract}\n\n"
                        f"Dimension-specific calibration guidance:\n"
                        f"{_dimension_calibration_guidance(dimension)}\n\n"
                        f"Paper map:\n{paper_map}"
                ),
            },
            {
                "role": "user",
                "content": f"Q&A evidence:\n{qa_text}",
            },
        ],
    )


def _load_dimension_review_prompt(config: dict, dimension: str) -> str:
    """Load dimension-specific review-writer guidance."""
    prompt_name = f"prompts/{dimension.lower()}_review_writer_guidance.md"
    try:
        return load_prompt(prompt_name, config=config).strip()
    except FileNotFoundError:
        return ""


def _dimension_calibration_guidance(dimension: str) -> str:
    """Return dimension-specific scoring priorities for the review writer."""
    if dimension == "Soundness":
        return (
            "Soundness priority order: central-claim validity; evaluation/protocol "
            "correctness; baseline fairness; statistical reliability; direct validation "
            "of headline claims; reproducibility details; secondary ablations. Score by "
            "the claim_effect of each confirmed decisive issue, and do not default. Treat "
            "a weakness as `local` (keeps `3 good`) unless it specifically threatens the "
            "main claims; ordinary gaps (a missing ablation, a broader comparison, "
            "uncertainty estimates, narrow scope) are `local`. A confirmed weakness that "
            "invalidates the central claim, evaluation validity, or reproducibility forces "
            "`2 fair` or `1 poor`, and no strength or large reported margin can raise the "
            "score above it. A confirmed weakness that materially weakens the main value "
            "maps to `2 fair` only when the main claim is genuinely in doubt, otherwise "
            "`3 good`; it is not an automatic `2`. Reserve materially_weakens/invalidates "
            "for the 1-2 weaknesses that truly threaten the central claim. Anchor to "
            "`3 good` for a paper with real but non-fatal limitations: naming a decisive "
            "issue does not by itself force `2` (a decisive issue may be `local`, or a "
            "`materially_weakens` that the main claim survives, and keep `3`). Reserve `2` "
            "for a confirmed issue that genuinely puts the central claim, evaluation "
            "validity, or reproducibility in real doubt — not for ordinary validation gaps. "
            "Conversely, when no confirmed claim-invalidating or main-value-shaking weakness "
            "remains, use `3 good` for mostly-supported claims and `4 excellent` for claims "
            "strongly supported by rigorous evidence. An unconfirmed or low-confidence "
            "concern should not by itself lower the score."
        )
    if dimension == "Contribution":
        return (
            "Contribution priority order: novelty relative to closest prior work; "
            "importance of the problem; breadth and generality; empirical/practical "
            "impact; benchmark or artifact value; incremental engineering value. "
            "Use ICLR 2026 calibration: state-of-the-art results are not required, and "
            "incremental or specialized work can be `3 good` when it convincingly "
            "demonstrates new, relevant, useful knowledge for the community. Use `2 fair` "
            "when the new knowledge or likely value remains limited after accounting for "
            "evidence, positioning, and scope. System integration can score well when the "
            "integrated capability, analysis, artifact, or empirical result is meaningful "
            "beyond an expected combination. Use `4 excellent` when the contribution is "
            "clearly important or likely impactful by ICLR standards; use `1 poor` when "
            "there is little supported new knowledge or value."
        )
    if dimension == "Presentation":
        return (
            "Presentation priority order: whether a reviewer can understand and evaluate "
            "the method/results; whether key definitions, algorithms, protocols, and claims "
            "are self-contained; whether figures/tables are readable enough to verify "
            "claims; reproducibility/navigation; polish. Do not let local visual polish "
            "dominate unless it blocks assessment. Do not treat unavailable tool evidence "
            "as a paper weakness. A readable paper with missing central protocol or method "
            "details can be `2 fair`, while ordinary readability alone is not `4 excellent`."
        )
    return (
        "Prioritize C0/C1/C2 findings by decision impact, not by count. Use adjacent-score "
        "boundary reasoning and calibrate to the active reviewer guide rather than to a strict or lenient default."
    )


def _validate_dimension_review_contract(xml_text: str) -> None:
    """Require dimension review fields that downstream aggregation depends on."""
    root = ET.fromstring(xml_text)
    decisive_issues = root.find("decisive_issues")
    if decisive_issues is None:
        raise ValueError(
            "The dimension_review must include a <decisive_issues> section with 1-2 human-reviewer score-bound issues."
        )
    decisive_items = [
        item
        for item in decisive_issues.findall("item")
        if "".join(item.itertext()).strip()
    ]
    if not decisive_items:
        raise ValueError(
            "The dimension_review <decisive_issues> section must include at least one non-empty <item>."
        )
    if len(decisive_items) > 2:
        raise ValueError(
            "The dimension_review <decisive_issues> section should include at most two <item> entries."
        )
    for item in decisive_items:
        if not item.attrib.get("qa_ids"):
            raise ValueError("Each decisive_issues item must include a qa_ids attribute.")
        if not item.attrib.get("dimension_score_cap"):
            raise ValueError(
                "Each decisive_issues item must include a dimension_score_cap attribute."
            )

    _validate_score_consistency(root, decisive_items)

    judgment = root.find("dimension_judgment")
    if judgment is None:
        raise ValueError(
            "The dimension_review must include a <dimension_judgment> section with the evidence-derived dimension thesis."
        )
    if not _child_text(judgment, "judgment_posture"):
        raise ValueError(
            "The dimension_review <dimension_judgment> must include <judgment_posture>."
        )
    if not _child_text(judgment, "main_thesis"):
        raise ValueError(
            "The dimension_review <dimension_judgment> must include <main_thesis>."
        )

    key_points = root.find("key_points")
    if key_points is None:
        raise ValueError(
            "The dimension_review must include a <key_points> section listing every "
            "decision-relevant and actionable scored finding (no maximum)."
        )
    items = [
        item
        for item in key_points.findall("item")
        if "".join(item.itertext()).strip()
    ]
    if not items:
        raise ValueError(
            "The dimension_review <key_points> section must include at least one non-empty <item>."
        )
    for item in items:
        if not item.attrib.get("importance"):
            raise ValueError("Each key_points item must include an importance attribute.")
        if not item.attrib.get("polarity"):
            raise ValueError("Each key_points item must include a polarity attribute.")
        if not item.attrib.get("confidence"):
            raise ValueError("Each key_points item must include a confidence attribute.")
        if not item.attrib.get("evidence_status"):
            raise ValueError("Each key_points item must include an evidence_status attribute.")


def _validate_score_consistency(root: ET.Element, decisive_items: list[ET.Element]) -> None:
    """Enforce that the dimension score is consistent with its own decisive evidence.

    Bidirectional rule (down-direction is hard-enforced here; the up-direction is
    prompt-guided): a confirmed decisive weakness tagged claim_effect="invalidates"
    cannot be scored above 2, and no strength may rescue it. The check is a no-op
    when the optional claim_effect attribute is absent, so it is backward
    compatible with reviews that do not tag it.
    """
    score_el = root.find("score")
    score_text = (score_el.text or "").strip() if score_el is not None else ""
    score_val = int(score_text[0]) if score_text[:1] in {"1", "2", "3", "4"} else None
    if score_val is None:
        return

    def _attr(item: ET.Element, name: str) -> str:
        return str(item.attrib.get(name, "")).strip().lower()

    invalidating = [
        item
        for item in decisive_items
        if _attr(item, "polarity") == "weakness"
        and _attr(item, "claim_effect") == "invalidates"
        and _attr(item, "evidence_status") == "confirmed"
    ]
    if invalidating and score_val > 2:
        raise ValueError(
            'A confirmed decisive weakness is marked claim_effect="invalidates", so '
            "the dimension <score> must be 1 or 2 (use 1 when the paper becomes "
            "non-assessable). A strength, strong baselines, or a large reported margin "
            "cannot raise the score above a confirmed claim-invalidating flaw. Either "
            f"lower <score> to 1 or 2 (current score is {score_val}), or, if the issue "
            "does not truly invalidate the central claim, change its claim_effect to "
            '"materially_weakens"/"local" or its evidence_status away from "confirmed".'
        )


def _child_text(root: ET.Element, name: str) -> str:
    """Read child text from an XML element."""
    child = root.find(name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()

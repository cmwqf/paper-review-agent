"""Purpose: Answer Agent scaffold.

The Answer Agent answers one dimension-specific review question. Unlike a plain
answer model, it is allowed to decide whether it needs paper-local evidence,
external retrieval evidence, or both before writing the final QAResult.

Planned loop:

1. Observe question, dimension, paper map, and compact prior context.
2. Choose a tool_call: search_file, read_file, inspect_visual, search_scholar,
   or write qa_result.
3. Use tools to gather evidence.
4. Write `<qa_result>` with answer, evidence summary, trace refs, and review impact.

Raw paper chunks and retrieval results should be stored in the full trace, not
blindly carried into the next Agent prompt.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError

from reviewer.agents.base import BaseAgent
from reviewer.models.factory import build_llm
from reviewer.schemas.qa import QAResult, parse_qa_result_xml
from reviewer.schemas.summary import SummarySchema, render_summary_for_agent
from reviewer.tools.paper_read_tool import PaperReadTool
from reviewer.tools.paper_search_tool import PaperSearchTool
from reviewer.tools.retrieval_tool import RetrievalTool
from reviewer.tools.visual_inspection_tool import VisualInspectionTool
from reviewer.tools.xml_validator import extract_xml_document, validate_xml_root
from reviewer.utils.prompts import load_prompt, load_rubric_prompt


class AnswerAgent(BaseAgent):
    """Evidence-seeking agent that produces structured QAResult objects."""

    name = "answer"

    def run(
        self,
        question: str,
        dimension: str,
        paper: dict,
        paper_summary: dict | str,
        prior_qa_results: list[QAResult] | None = None,
    ) -> QAResult:
        """Answer one review question with evidence and review impact.

        The agent repeatedly asks the LLM for one tool call. Tool observations
        are appended to the next step. The loop stops when the model emits a
        `<qa_result>` document.
        """
        model_key = self.config.get("agents", {}).get(dimension.lower(), {}).get(
            "answer_model", "answer"
        )
        client = build_llm(self.config, model_key)
        observations: list[str] = []
        retrieved_papers: list[dict] = []
        trace_events: list[dict] = []
        format_feedback = ""
        prior_qa_results = prior_qa_results or []
        max_steps = int(self.config.get("qa", {}).get("max_answer_steps", 6))
        paper_map = _render_paper_summary(paper_summary)
        system_prompt = _answer_system_prompt(self.config, dimension)

        for step_index in range(max_steps):
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": _build_action_context(
                        question=question,
                        dimension=dimension,
                        paper=paper,
                        paper_map=paper_map,
                        observations=observations,
                        retrieved_papers=retrieved_papers,
                        prior_qa_results=prior_qa_results,
                        format_feedback=format_feedback,
                    ),
                },
            ]
            raw_output = client.generate(messages)
            format_feedback = ""
            trace_events.append(
                {
                    "agent": "answer",
                    "event": "model_output",
                    "step": step_index + 1,
                    "dimension": dimension,
                    "question": question,
                    "raw_output": raw_output,
                }
            )
            violation = _output_contract_violation(raw_output)
            if violation:
                format_feedback = violation
                trace_events.append(
                    {
                        "agent": "answer",
                        "event": "output_contract_violation",
                        "step": step_index + 1,
                        "dimension": dimension,
                        "question": question,
                        "feedback": violation,
                    }
                )
                continue
            try:
                action_xml = extract_xml_document(raw_output, "tool_call")
                has_tool_call = (
                    action_xml != raw_output.strip() or raw_output.strip().startswith("<tool_call")
                )
                if has_tool_call:
                    action = _parse_action(action_xml)
                else:
                    qa_xml = extract_xml_document(raw_output, "qa_result")
                    if qa_xml != raw_output.strip() or raw_output.strip().startswith("<qa_result"):
                        result = parse_qa_result_xml(qa_xml)
                        _attach_retrieved_paper_details(result, retrieved_papers)
                        result.trace_events = trace_events
                        return result
                    action = _parse_action(raw_output)
            except (ValueError, ParseError):
                trace_events.append(
                    {
                        "agent": "answer",
                        "event": "parse_error",
                        "step": step_index + 1,
                        "dimension": dimension,
                        "question": question,
                    }
                )
                continue
            observation, new_retrieved = _run_action(action, self.config, paper, question)
            trace_events.append(
                {
                    "agent": "answer",
                    "event": "tool_call",
                    "step": step_index + 1,
                    "dimension": dimension,
                    "question": question,
                    "action": action,
                }
            )
            trace_events.append(
                {
                    "agent": "answer",
                    "event": "tool_observation",
                    "step": step_index + 1,
                    "dimension": dimension,
                    "question": question,
                    "action": action,
                    "observation": observation,
                    "retrieved_papers": new_retrieved,
                }
            )
            observations.append(observation)
            retrieved_papers.extend(new_retrieved)

        result = _write_forced_answer(
            client=client,
            config=self.config,
            question=question,
            dimension=dimension,
            paper_map=paper_map,
            observations=observations,
            retrieved_papers=retrieved_papers,
        )
        _attach_retrieved_paper_details(result, retrieved_papers)
        result.trace_events = trace_events
        return result


def _answer_system_prompt(config: dict, dimension: str) -> str:
    """Build the Answer Agent system prompt with the action XML contract."""
    prompt = load_prompt("prompts/answer_agent.md", config=config)
    rubric_prompt = load_rubric_prompt(config)
    dimension_prompt = _load_dimension_answer_prompt(config, dimension)
    qa_contract = load_prompt("prompts/qa_answer_xml.md", config=config)
    action_contract = """
For tool-use steps, return exactly one `<tool_call>` XML document. A response
with more than one `<tool_call>` is invalid. A response that contains both
`<tool_call>` and `<qa_result>` is invalid.

<tool_call>
  <tool_name>search_file | read_file | inspect_visual | search_scholar</tool_name>
  <keyword>keyword or short phrase for search_file</keyword>
  <start_line>1-based start line for read_file</start_line>
  <num_lines>number of lines for read_file, max 50</num_lines>
  <target>one visual target for inspect_visual, such as Figure 2, Table 1, or page 4</target>
  <focus>optional focus for inspect_visual, such as axes/legend readability or page layout</focus>
  <query>concise scholarly query for search_scholar</query>
  <rationale>why this action is needed</rationale>
</tool_call>

Tool-use policy:

- Use `search_file` to locate relevant paper lines when you do not already know
  the exact line range. It works best with short paper-local keywords or exact
  phrases, such as method names, metric names, dataset names, section names, or
  distinctive terms from the paper map. Avoid using a long natural-language
  query when a shorter keyword would likely find the relevant text.
- Use `read_file` only for a specific bounded line range. It is not a
  full-paper reading tool and cannot read the whole paper in one call.
- Use `search_scholar` when external prior-work evidence is needed. It works
  best with a concise scholarly search query: a research topic, method family,
  or key claim. Avoid copying the full review question when a shorter topic
  phrase would capture the main prior-work comparison.
- Use `inspect_visual` for visual evidence about one specific figure, table, or
  PDF page. The tool routes Figure/Picture targets to extracted figure assets
  when available, and routes Table/page-layout targets to exactly one rendered
  PDF page. For table contents, use `search_file` and `read_file` instead.

When you have enough evidence, return `<qa_result>` directly.

Return exactly one XML document and nothing else. Never return multiple
`<tool_call>` documents. Never return both `<tool_call>` and `<qa_result>` in
the same response. If several tools seem useful, choose only the single
highest-value next tool.
"""
    return f"{rubric_prompt}\n\n{prompt}\n\n{dimension_prompt}\n\n{action_contract}\n\n{qa_contract}"


def _load_dimension_answer_prompt(config: dict, dimension: str) -> str:
    """Load dimension-specific Answer Agent guidance."""
    prompt_name = f"prompts/answer_{dimension.lower()}_agent.md"
    try:
        return load_prompt(prompt_name, config=config)
    except FileNotFoundError:
        return ""


def _render_paper_summary(paper_summary: dict | str) -> str:
    """Render summary input into compact text."""
    if isinstance(paper_summary, SummarySchema):
        return render_summary_for_agent(paper_summary)
    if isinstance(paper_summary, dict):
        return str(paper_summary)
    return str(paper_summary)


def _build_action_context(
    *,
    question: str,
    dimension: str,
    paper: dict,
    paper_map: str,
    observations: list[str],
    retrieved_papers: list[dict],
    prior_qa_results: list[QAResult] | None = None,
    format_feedback: str = "",
) -> str:
    """Build the model-visible state for one Answer Agent step."""
    observed = "\n\n".join(observations[-8:]) if observations else "No observations yet."
    retrieved = "\n\n".join(_format_retrieved_paper(paper) for paper in retrieved_papers[:8])
    if not retrieved:
        retrieved = "No retrieved papers yet."
    prior_qa = _format_prior_qa_results(prior_qa_results or [])
    visual_assets = _format_visual_assets(paper)
    metadata = paper.get("metadata", {})
    feedback = f"\n\nPrevious output format error:\n{format_feedback}\n" if format_feedback else ""
    return (
        f"Review dimension: {dimension}\n"
        f"Question: {question}\n\n"
        f"Paper metadata:\n{metadata}\n\n"
        f"Prior Q&A in this dimension for impact calibration:\n{prior_qa}\n\n"
        f"Paper summary / map:\n{paper_map}\n\n"
        f"Available visual assets for inspect_visual:\n{visual_assets}\n\n"
        f"Tool observations:\n{observed}\n\n"
        f"Retrieved papers:\n{retrieved}\n"
        f"{feedback}"
    )


def _format_prior_qa_results(qa_results: list[QAResult]) -> str:
    """Render compact prior Q&A so impact labels are calibrated across the dimension."""
    if not qa_results:
        return "No prior Q&A results yet."
    lines = []
    for index, result in enumerate(qa_results[-8:], 1):
        impact = result.review_impact
        lines.append(
            f"Q{index}: {result.question}\n"
            f"Answer: {result.answer}\n"
            f"Prior impact: {impact.polarity}, {impact.impact_level}, confidence={impact.confidence}"
        )
    return "\n\n".join(lines)


def _format_visual_assets(paper: dict) -> str:
    """Render a compact list of available extracted figure assets."""
    assets = paper.get("figures") or []
    if not isinstance(assets, list) or not assets:
        return "No extracted figure assets are listed. inspect_visual can still inspect Table N or page N via PDF page rendering."
    lines = []
    for asset in assets[:40]:
        label = str(asset.get("label") or "").strip()
        page = asset.get("pdf_page")
        if not label:
            continue
        page_text = f", PDF page {page}" if page else ""
        lines.append(f"- {label}{page_text}")
    if len(assets) > 40:
        lines.append(f"- ... {len(assets) - 40} more figure assets omitted")
    return "\n".join(lines) if lines else "No extracted figure assets are listed."


def _output_contract_violation(raw_output: str) -> str:
    """Return retry feedback when a model emits more than one XML document."""
    tool_call_count = raw_output.count("<tool_call")
    qa_result_count = raw_output.count("<qa_result")
    if tool_call_count > 1:
        return (
            "Invalid output: you returned multiple <tool_call> documents. "
            "Return exactly one XML document: either one <tool_call> or one <qa_result>, never more."
        )
    if tool_call_count and qa_result_count:
        return (
            "Invalid output: you returned both <tool_call> and <qa_result>. "
            "Return exactly one XML document. If more evidence is needed, return one <tool_call>; "
            "otherwise return one <qa_result>."
        )
    if qa_result_count > 1:
        return "Invalid output: you returned multiple <qa_result> documents. Return exactly one."
    return ""


def _parse_action(raw_output: str) -> dict[str, str]:
    """Parse a `<tool_call>` XML document."""
    action_xml = validate_xml_root(raw_output, "tool_call")
    root = ET.fromstring(action_xml)
    return {
        "action": _child_text(root, "tool_name"),
        "keyword": _child_text(root, "keyword"),
        "start_line": _child_text(root, "start_line"),
        "num_lines": _child_text(root, "num_lines"),
        "target": _child_text(root, "target"),
        "focus": _child_text(root, "focus"),
        "query": _child_text(root, "query"),
        "rationale": _child_text(root, "rationale"),
    }


def _run_action(
    action: dict[str, str],
    config: dict,
    paper: dict,
    question: str,
) -> tuple[str, list[dict]]:
    """Run one Answer Agent tool action and return prompt observation plus retrieval additions."""
    action_name = action.get("action", "").strip()
    try:
        if action_name == "search_file":
            keyword = action.get("keyword") or question
            observation = PaperSearchTool(config).search(keyword, paper, top_k=5, context_lines=2)
            return f"search_file({keyword!r})\n{observation}", []
        if action_name == "read_file":
            start_line = int(action.get("start_line") or "1")
            num_lines = int(action.get("num_lines") or "30")
            observation = PaperReadTool(config).read(paper, start_line=start_line, num_lines=num_lines)
            return f"read_file(start_line={start_line}, num_lines={num_lines})\n{observation}", []
        if action_name == "inspect_visual":
            target = action.get("target") or question
            focus = action.get("focus") or ""
            observation = VisualInspectionTool(config).inspect(paper, target=target, focus=focus)
            return f"inspect_visual(target={target!r}, focus={focus!r})\n{observation}", []
        if action_name == "search_scholar":
            query = action.get("query") or question
            papers = RetrievalTool(config).search(query, paper.get("metadata", {}))
            rendered = "\n\n".join(_format_retrieved_paper(item) for item in papers[:8])
            return f"search_scholar({query!r})\n{rendered or 'No retrieved papers.'}", papers
    except Exception as exc:
        return f"{action_name} failed: {exc}", []
    return f"Unsupported action: {action_name}", []


def _format_retrieved_paper(paper: dict) -> str:
    """Render a retrieved paper with the abstract visible to the Answer Agent."""
    title = paper.get("title") or ""
    year = paper.get("year") or ""
    citations = paper.get("citation_count")
    abstract = paper.get("abstract") or "No abstract returned."
    citation_text = f", citations={citations}" if citations is not None else ""
    return (
        f"- Title: {title}\n"
        f"  Year: {year}{citation_text}\n"
        f"  Abstract: {abstract}"
    )


def _attach_retrieved_paper_details(result: QAResult, retrieved_papers: list[dict]) -> None:
    """Preserve tool-returned abstracts in the structured QA artifact."""
    if not retrieved_papers:
        return
    by_title = {
        str(paper.get("title", "")).strip().lower(): paper
        for paper in retrieved_papers
        if paper.get("title")
    }
    by_url = {
        str(paper.get("url", "")).strip(): paper
        for paper in retrieved_papers
        if paper.get("url")
    }
    if not result.retrieved_papers:
        result.retrieved_papers = retrieved_papers[:8]
        return
    enriched = []
    for paper in result.retrieved_papers:
        source = (
            by_url.get(str(paper.get("url", "")).strip())
            or by_title.get(str(paper.get("title", "")).strip().lower())
        )
        if source:
            merged = dict(source)
            merged.update({key: value for key, value in paper.items() if value not in (None, "")})
            enriched.append(merged)
        else:
            enriched.append(paper)
    result.retrieved_papers = enriched


def _write_forced_answer(
    *,
    client,
    config: dict,
    question: str,
    dimension: str,
    paper_map: str,
    observations: list[str],
    retrieved_papers: list[dict],
) -> QAResult:
    """Ask the model to produce a final answer after action budget is exhausted."""
    qa_contract = load_prompt("prompts/qa_answer_xml.md", config=config)
    messages = [
        {
            "role": "system",
            "content": (
                "Write the final Q&A answer now. Do not request more tools.\n\n"
                f"{qa_contract}"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Review dimension: {dimension}\nQuestion: {question}\n\n"
                f"Paper map:\n{paper_map}\n\n"
                f"Observations:\n{chr(10).join(observations)}\n\n"
                f"Retrieved papers:\n{retrieved_papers[:8]}"
            ),
        },
    ]
    return parse_qa_result_xml(client.generate(messages))


def _child_text(root: ET.Element, name: str) -> str:
    """Read child text from an XML element."""
    child = root.find(name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()

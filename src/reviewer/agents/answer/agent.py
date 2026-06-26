"""Purpose: Answer Agent scaffold.

The Answer Agent answers one dimension-specific review question. Unlike a plain
answer model, it is allowed to decide whether it needs paper-local evidence,
external retrieval evidence, or both before writing the final QAResult.

Planned loop:

1. Observe question, dimension, paper map, and compact prior context.
2. Write exactly one `<action>`.
3. Execute the requested evidence tool, or finish when the tool is `end_answer`.

Raw paper chunks and retrieval results should be stored in the full trace, not
blindly carried into the next Agent prompt.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from typing import Any

from reviewer.agents.base import BaseAgent
from reviewer.models.factory import build_llm
from reviewer.schemas.qa import QAResult, parse_qa_result_xml
from reviewer.schemas.summary import SummarySchema, render_summary_for_agent
from reviewer.tools.paper_read_tool import PaperReadTool
from reviewer.tools.paper_search_tool import PaperSearchTool
from reviewer.tools.python_tool import RestrictedPythonTool
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

        The agent repeatedly asks the LLM for exactly one `<action>`.
        Evidence tools add observations to the next step. The special
        `end_answer` tool carries the final answer fields and exits this run.
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
        qa_config = self.config.get("qa", {})
        max_steps = int(qa_config.get("max_answer_steps", 6))
        max_format_retries = int(qa_config.get("max_format_retries", 3))
        max_format_attempts = max(1, max_format_retries + 1)
        paper_map = _render_paper_summary(paper_summary)
        # Stable per-paper context (metadata, paper map, visual assets) goes in
        # the system prompt so it stays byte-identical across this answer call's
        # steps and Claude Code reuses the prompt cache instead of recreating it.
        system_prompt = _answer_cached_system(
            _answer_system_prompt(self.config, dimension), paper, paper_map
        )

        step_index = 0
        while step_index < max_steps:
            context = _build_answer_context(
                question=question,
                dimension=dimension,
                observations=observations,
                retrieved_papers=retrieved_papers,
                prior_qa_results=prior_qa_results,
                format_feedback=format_feedback,
            )
            try:
                action_xml = _write_tool_call(
                    client=client,
                    system_prompt=system_prompt,
                    context=context,
                    max_attempts=max_format_attempts,
                    trace_events=trace_events,
                    trace_base={
                        "agent": "answer",
                        "stage": "tool_call",
                        "step": step_index + 1,
                        "dimension": dimension,
                        "question": question,
                    },
                )
            except (RuntimeError, ValueError, ParseError) as exc:
                trace_events.append(
                    {
                        "agent": "answer",
                        "event": "tool_call_failed",
                        "stage": "tool_call",
                        "step": step_index + 1,
                        "dimension": dimension,
                        "question": question,
                        "error": str(exc),
                    }
                )
                break

            action = _parse_action(action_xml)
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
            if action["action"] == "end_answer":
                result = _parse_end_answer(action_xml)
                _attach_retrieved_paper_details(result, retrieved_papers)
                result.trace_events = trace_events
                return result

            format_feedback = ""
            observation, new_retrieved = _run_action(action, self.config, paper, question)
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
            step_index += 1

        result = _write_forced_answer(
            client=client,
            system_prompt=system_prompt,
            config=self.config,
            question=question,
            dimension=dimension,
            observations=observations,
            retrieved_papers=retrieved_papers,
            trace_events=trace_events,
        )
        _attach_retrieved_paper_details(result, retrieved_papers)
        result.trace_events = trace_events
        return result


def _answer_guidance_prompt(config: dict, dimension: str) -> str:
    """Build shared reviewer guidance without any output schema."""
    prompt = load_prompt("prompts/answer_agent_shared_guidance.md", config=config).strip()
    rubric_prompt = load_rubric_prompt(config)
    dimension_prompt = _load_dimension_answer_prompt(config, dimension)
    return f"{rubric_prompt}\n\n{prompt}\n\n{dimension_prompt}"


def _answer_system_prompt(config: dict, dimension: str) -> str:
    """Build the Answer Agent prompt with the single tool-call XML contract."""
    guidance = _answer_guidance_prompt(config, dimension)
    tool_contract = """
TOOL-CALL STAGE

Every response must be exactly one `<action>` XML document and nothing else.
Do not output `<qa_result>`, `<answer_decision>`, markdown fences, explanatory
text, or multiple XML documents.

Choose exactly one tool per turn. Use evidence tools when more evidence is
needed. Use `end_answer` when the current observations are enough; after a
valid `end_answer`, this AnswerAgent run exits and the dimension agent may ask
the next query.

<action>
  <tool_name>search_file | read_file | inspect_visual | search_scholar | run_python | end_answer</tool_name>
  <keyword>keyword or short phrase for search_file</keyword>
  <start_line>1-based start line for read_file</start_line>
  <num_lines>number of lines for read_file, max 50</num_lines>
  <target>one visual target for inspect_visual, such as Figure 2, Table 1, or page 4</target>
  <focus>optional focus for inspect_visual, such as axes/legend readability or page layout</focus>
  <query>concise scholarly query for search_scholar</query>
  <code><![CDATA[
small self-contained Python code for run_python
]]></code>

  <!-- end_answer fields; use these only when tool_name is end_answer -->
  <question>repeat the active question</question>
  <answer>final answer grounded in evidence</answer>
  <evidence>
    <item source="paper">paper text evidence</item>
    <item source="visual">visual/PDF evidence</item>
    <item source="retrieval">retrieved prior-work evidence</item>
    <item source="inference">carefully marked reviewer inference</item>
  </evidence>
  <retrieved_papers>
    <paper>
      <title>...</title>
      <abstract>...</abstract>
      <year>...</year>
      <relevance>...</relevance>
    </paper>
  </retrieved_papers>
  <review_impact>
    <dimension>Contribution | Soundness | Presentation</dimension>
    <polarity>strength | weakness</polarity>
    <impact_level>C0 | C1 | C2 | C3 | C4</impact_level>
    <confidence>low | medium | high</confidence>
  </review_impact>

  <rationale>why this action is needed</rationale>
</action>

For evidence tools, include only the tool_name, that tool's arguments, and
rationale. Do not include answer, evidence, retrieved_papers, or review_impact.
For `end_answer`, include question, answer, evidence, retrieved_papers,
review_impact, and rationale. Do not include evidence-tool arguments.

Tool-use policy:

- Use `search_file` to locate relevant paper lines when you do not already know
  the exact line range. It works best with short paper-local keywords or exact
  phrases, such as method names, metric names, dataset names, section names, or
  distinctive terms from the paper map. Avoid using a long natural-language
  query when a shorter keyword would likely find the relevant text.
  If search_file returns no matches, try a broader or more literal paper-local
  keyword before concluding the paper lacks the evidence. Prefer exact terms
  that are likely to appear in the PDF text, such as "Table 1", "Theorem 3.2",
  "ablation", "limitations", a dataset name, or a method name.
- Use `read_file` only for a specific bounded line range. It is not a
  full-paper reading tool and cannot read the whole paper in one call.
  After a useful search_file result, prefer using read_file on the most relevant
  line range before writing the QAResult.
- Use `search_scholar` when external prior-work evidence is needed. It works
  best with a short keyword query, not a full review question or sentence. Use
  3-7 core terms: one problem setting, one method family, and optionally one
  metric/claim term. Avoid combining many authors, metrics, and claims in one
  query. If a search_scholar observation returns no useful papers, the next
  search_scholar query should be broader and shorter than the failed query.
- Use `inspect_visual` for visual evidence about one specific figure, table, or
  PDF page. The tool routes Figure/Picture targets to extracted figure assets
  when available, and routes Table/page-layout targets to exactly one rendered
  PDF page. For table contents, use `search_file` and `read_file` instead.
- Use `run_python` only for small, self-contained calculations over evidence
  already visible in the prompt, such as relative improvements, averages,
  simple formula checks, parsing numeric snippets, or toy counterexamples. It
  has no network access and must not attempt web search, file I/O, subprocesses,
  package installation, shell commands, environment access, or filesystem
  inspection. If you need paper evidence, use `search_file`/`read_file` first.
  If you need prior-work evidence, use `search_scholar`.

Examples of search_scholar query style:

- Bad: a full review question with many authors, metrics, and claims
- Good: finite-sum variational inequality variance reduction
- Good: language model calibration RLHF confidence

Impact levels for `end_answer`:

- C0: confirmed hard-gate or non-reviewability issue.
- C1: decisive score-driving point.
- C2: important review point that should usually appear in the dimension review.
- C3: local actionable point.
- C4: minor polish, speculative/low-confidence, or trace-only note.

Always choose either strength or weakness. Do not use neutral or mixed. Do not
use C2 as a safe default.
"""
    return f"{guidance}\n\n{tool_contract}"


def _load_dimension_answer_prompt(config: dict, dimension: str) -> str:
    """Load dimension-specific Answer Agent guidance."""
    prompt_name = f"prompts/answer_agent_{dimension.lower()}_guidance.md"
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


def _answer_cached_system(system_prompt: str, paper: dict, paper_map: str) -> str:
    """Append stable per-paper context to the system prompt for cache reuse.

    Metadata, the paper map, and the visual-asset list are identical across an
    answer call's steps, so anchoring them in the system prompt lets Claude
    Code's prompt cache be read rather than recreated on each step.
    """
    return (
        f"{system_prompt}\n\n"
        f"Paper metadata:\n{paper.get('metadata', {})}\n\n"
        f"Paper summary / map:\n{paper_map}\n\n"
        f"Available visual assets for inspect_visual:\n{_format_visual_assets(paper)}"
    )


def _build_answer_context(
    *,
    question: str,
    dimension: str,
    observations: list[str],
    retrieved_papers: list[dict],
    prior_qa_results: list[QAResult] | None = None,
    format_feedback: str = "",
) -> str:
    """Build the turn-varying evidence state for one Answer Agent step.

    Stable paper context (metadata, map, visual assets) is supplied via the
    system prompt by :func:`_answer_cached_system`; only per-step state is here.
    """
    observed = "\n\n".join(observations[-8:]) if observations else "No observations yet."
    retrieved = "\n\n".join(_format_retrieved_paper(paper) for paper in retrieved_papers[:8])
    if not retrieved:
        retrieved = "No retrieved papers yet."
    prior_qa = _format_prior_qa_results(prior_qa_results or [])
    feedback = f"\n\nPrevious output format error:\n{format_feedback}\n" if format_feedback else ""
    return (
        f"Review dimension: {dimension}\n"
        f"Question: {question}\n\n"
        f"Prior Q&A in this dimension for impact calibration:\n{prior_qa}\n\n"
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


def _write_tool_call(
    *,
    client: Any,
    system_prompt: str,
    context: str,
    max_attempts: int,
    trace_events: list[dict],
    trace_base: dict[str, Any],
) -> str:
    """Ask the model for exactly one AnswerAgent tool call."""
    return _generate_stage_xml(
        client=client,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"{context}\n\n"
                    "Output EXACTLY ONE <action> XML document this turn — one "
                    "action only. If you emit more than one <action>, only the "
                    "FIRST is executed and the rest are ignored, so never batch "
                    "actions. Choose one evidence tool, or tool_name=end_answer to finish."
                ),
            },
        ],
        root_tag="action",
        disallowed_roots=("answer_decision", "qa_result"),
        max_attempts=max_attempts,
        trace_events=trace_events,
        trace_base=trace_base,
        validator=_validate_tool_call_xml,
    )


def _generate_stage_xml(
    *,
    client: Any,
    messages: list[dict[str, Any]],
    root_tag: str,
    disallowed_roots: tuple[str, ...],
    max_attempts: int,
    trace_events: list[dict] | None = None,
    trace_base: dict[str, Any] | None = None,
    validator=None,
) -> str:
    """Generate one strict XML document for a runtime stage."""
    current_messages = list(messages)
    last_error: Exception | None = None
    last_output = ""
    for attempt in range(1, max(1, int(max_attempts)) + 1):
        raw_output = client.generate(current_messages)
        last_output = raw_output
        if trace_events is not None:
            trace_events.append(
                {
                    **(trace_base or {}),
                    "event": "model_output",
                    "attempt": attempt,
                    "raw_output": raw_output,
                }
            )
        try:
            clean_xml = _validate_single_stage_xml(raw_output, root_tag, disallowed_roots)
            if validator is not None:
                validator(clean_xml)
            return clean_xml
        except Exception as exc:
            last_error = exc
            if trace_events is not None:
                trace_events.append(
                    {
                        **(trace_base or {}),
                        "event": "stage_contract_violation",
                        "attempt": attempt,
                        "error": str(exc),
                    }
                )
            if attempt >= max(1, int(max_attempts)):
                break
            current_messages = [
                *messages,
                {"role": "assistant", "content": raw_output},
                {
                    "role": "user",
                    "content": (
                        f"The previous output was not valid <{root_tag}> stage XML.\n"
                        f"Parser error: {type(exc).__name__}: {exc}\n\n"
                        f"Regenerate exactly one <{root_tag}> document and nothing else. "
                        f"Do not include any of these tags: {', '.join(disallowed_roots)}. "
                        "Do not wrap it in markdown fences. Escape all literal &, <, and > "
                        "characters in text content as XML entities."
                    ),
                },
            ]
    assert last_error is not None
    raise RuntimeError(
        f"Could not generate valid <{root_tag}> stage XML after {max_attempts} attempts: "
        f"{type(last_error).__name__}: {last_error}\nLast output:\n{last_output}"
    )


def _validate_single_stage_xml(
    raw_output: str,
    root_tag: str,
    disallowed_roots: tuple[str, ...],
) -> str:
    """Validate the stage XML, tolerating extra/multiple tool-call documents.

    The model sometimes emits several <root_tag> documents (or wraps one in
    prose). Since the answer loop executes one action per step, we use the first
    document rather than rejecting and wasting a retry. A disallowed stage root
    (the wrong stage's output) is still a hard error.
    """
    if raw_output.count(f"<{root_tag}") == 0:
        raise ValueError(f"Expected a <{root_tag}> document, found none.")
    for disallowed in disallowed_roots:
        if raw_output.count(f"<{disallowed}"):
            raise ValueError(
                f"Invalid state output: <{root_tag}> stage must not contain <{disallowed}>."
            )
    extracted = extract_xml_document(raw_output, root_tag)
    return validate_xml_root(extracted, root_tag)


def _validate_tool_call_xml(xml_text: str, *, force_end_answer: bool = False) -> None:
    """Validate the single action contract, including end_answer arguments."""
    root = ET.fromstring(xml_text)
    tool_name = _child_text(root, "tool_name").strip()
    valid_tools = {
        "search_file",
        "read_file",
        "inspect_visual",
        "search_scholar",
        "run_python",
        "end_answer",
    }
    if tool_name not in valid_tools:
        raise ValueError(f"Unsupported AnswerAgent tool_name: {tool_name!r}")
    if force_end_answer and tool_name != "end_answer":
        raise ValueError("Tool budget exhausted; tool_name must be end_answer.")

    final_fields = ("question", "answer", "evidence", "retrieved_papers", "review_impact")
    tool_arg_fields = ("keyword", "start_line", "num_lines", "target", "focus", "query", "code")
    if tool_name == "end_answer":
        for field in ("question", "answer", "review_impact"):
            if root.find(field) is None or not "".join(root.find(field).itertext()).strip():
                raise ValueError(f"end_answer requires <{field}>.")
        impact = root.find("review_impact")
        for field in ("dimension", "polarity", "impact_level", "confidence"):
            if not _child_text(impact, field):
                raise ValueError(f"end_answer review_impact requires <{field}>.")
        for field in tool_arg_fields:
            child = root.find(field)
            if child is not None and "".join(child.itertext()).strip():
                raise ValueError(f"end_answer must not include tool argument <{field}>.")
        return

    for field in final_fields:
        child = root.find(field)
        if child is not None and "".join(child.itertext()).strip():
            raise ValueError(f"{tool_name} must not include final answer field <{field}>.")


def _parse_action(raw_output: str) -> dict[str, str]:
    """Parse a `<action>` XML document."""
    action_xml = validate_xml_root(raw_output, "action")
    root = ET.fromstring(action_xml)
    return {
        "action": _child_text(root, "tool_name"),
        "keyword": _child_text(root, "keyword"),
        "start_line": _child_text(root, "start_line"),
        "num_lines": _child_text(root, "num_lines"),
        "target": _child_text(root, "target"),
        "focus": _child_text(root, "focus"),
        "query": _child_text(root, "query"),
        "code": _child_text(root, "code"),
        "rationale": _child_text(root, "rationale"),
    }


def _parse_end_answer(raw_output: str) -> QAResult:
    """Parse an end_answer `<action>` into the QAResult schema."""
    action_xml = validate_xml_root(raw_output, "action")
    _validate_tool_call_xml(action_xml)
    root = ET.fromstring(action_xml)
    if _child_text(root, "tool_name") != "end_answer":
        raise ValueError("Expected end_answer action.")
    root.tag = "qa_result"
    for child_name in ("tool_name", "rationale"):
        child = root.find(child_name)
        if child is not None:
            root.remove(child)
    return parse_qa_result_xml(ET.tostring(root, encoding="unicode"))


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
        if action_name == "run_python":
            code = action.get("code", "")
            observation = RestrictedPythonTool(config).run(code).render()
            return f"run_python\n{observation}", []
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
    system_prompt: str,
    config: dict,
    question: str,
    dimension: str,
    observations: list[str],
    retrieved_papers: list[dict],
    trace_events: list[dict] | None = None,
) -> QAResult:
    """Ask the model to produce a final answer after action budget is exhausted."""
    max_attempts = int(config.get("xml", {}).get("max_generation_attempts", 5))
    observations_text = "\n".join(observations) if observations else "No observations were collected."
    action_xml = _generate_stage_xml(
        client=client,
        messages=[
            {
                # The paper map lives in the cache-anchored system_prompt.
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": (
                    f"Review dimension: {dimension}\nQuestion: {question}\n\n"
                    f"Observations:\n{observations_text}\n\n"
                    f"Retrieved papers:\n{retrieved_papers[:8]}\n\n"
                    "The AnswerAgent tool budget is exhausted. Return exactly one "
                    "<action> with <tool_name>end_answer</tool_name>. Do not "
                    "request another evidence tool."
                ),
            },
        ],
        root_tag="action",
        disallowed_roots=("answer_decision", "qa_result"),
        max_attempts=max_attempts,
        trace_events=trace_events,
        trace_base={
            "agent": "answer",
            "stage": "forced_end_answer",
            "dimension": dimension,
            "question": question,
            "forced_answer": True,
        },
        validator=lambda xml_text: _validate_tool_call_xml(xml_text, force_end_answer=True),
    )
    return _parse_end_answer(action_xml)


def _child_text(root: ET.Element, name: str) -> str:
    """Read child text from an XML element."""
    child = root.find(name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()

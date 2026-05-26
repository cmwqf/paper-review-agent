"""Purpose: Answer Agent scaffold.

The Answer Agent answers one dimension-specific review question. Unlike a plain
answer model, it is allowed to decide whether it needs paper-local evidence,
external retrieval evidence, or both before writing the final QAResult.

Planned loop:

1. Observe question, dimension, paper map, and compact prior context.
2. Choose a tool_call: search_file, read_file, search_scholar, or write qa_result.
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
from reviewer.tools.pdf_read_tool import PaperPDFReadTool
from reviewer.tools.retrieval_tool import RetrievalTool
from reviewer.tools.xml_validator import extract_xml_document, validate_xml_root
from reviewer.utils.prompts import load_prompt


class AnswerAgent(BaseAgent):
    """Evidence-seeking agent that produces structured QAResult objects."""

    name = "answer"

    def run(self, question: str, dimension: str, paper: dict, paper_summary: dict | str) -> QAResult:
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
                    ),
                },
            ]
            raw_output = client.generate(messages)
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
            try:
                action_xml = extract_xml_document(raw_output, "tool_call")
                has_tool_call = (
                    action_xml != raw_output.strip() or raw_output.strip().startswith("<tool_call")
                )
                if has_tool_call:
                    action = _parse_action(action_xml)
                    if "<qa_result" in raw_output:
                        trace_events.append(
                            {
                                "agent": "answer",
                                "event": "mixed_output_tool_call_prioritized",
                                "step": step_index + 1,
                                "dimension": dimension,
                                "question": question,
                            }
                        )
                else:
                    qa_xml = extract_xml_document(raw_output, "qa_result")
                    if qa_xml != raw_output.strip() or raw_output.strip().startswith("<qa_result"):
                        result = parse_qa_result_xml(qa_xml)
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
        result.trace_events = trace_events
        return result


def _answer_system_prompt(config: dict, dimension: str) -> str:
    """Build the Answer Agent system prompt with the action XML contract."""
    prompt = load_prompt("prompts/answer_agent.md", config=config)
    dimension_prompt = _load_dimension_answer_prompt(config, dimension)
    qa_contract = load_prompt("prompts/qa_answer_xml.md", config=config)
    action_contract = """
For tool-use steps, return exactly one `<tool_call>` XML document:

<tool_call>
  <tool_name>search_file | read_file | read_pdf | search_scholar</tool_name>
  <keyword>keyword for search_file</keyword>
  <start_line>1-based start line for read_file</start_line>
  <num_lines>number of lines for read_file, max 50</num_lines>
  <start_page>1-based start page for read_pdf</start_page>
  <num_pages>number of pages for read_pdf</num_pages>
  <query>query for search_scholar</query>
  <rationale>why this action is needed</rationale>
</tool_call>

When you have enough evidence, return `<qa_result>` directly.

Return exactly one XML document and nothing else. Never return multiple
`<tool_call>` documents. Never return both `<tool_call>` and `<qa_result>` in
the same response. If several tools seem useful, choose only the single
highest-value next tool.
"""
    return f"{prompt}\n\n{dimension_prompt}\n\n{action_contract}\n\n{qa_contract}"


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
) -> str:
    """Build the model-visible state for one Answer Agent step."""
    observed = "\n\n".join(observations[-8:]) if observations else "No observations yet."
    retrieved = "\n".join(
        f"- {paper.get('title')} ({paper.get('year')}): {paper.get('url')}"
        for paper in retrieved_papers[:8]
    )
    if not retrieved:
        retrieved = "No retrieved papers yet."
    metadata = paper.get("metadata", {})
    return (
        f"Review dimension: {dimension}\n"
        f"Question: {question}\n\n"
        f"Paper metadata:\n{metadata}\n\n"
        f"Paper summary / map:\n{paper_map}\n\n"
        f"Tool observations:\n{observed}\n\n"
        f"Retrieved papers:\n{retrieved}\n"
    )


def _parse_action(raw_output: str) -> dict[str, str]:
    """Parse a `<tool_call>` XML document."""
    action_xml = validate_xml_root(raw_output, "tool_call")
    root = ET.fromstring(action_xml)
    return {
        "action": _child_text(root, "tool_name"),
        "keyword": _child_text(root, "keyword"),
        "start_line": _child_text(root, "start_line"),
        "num_lines": _child_text(root, "num_lines"),
        "start_page": _child_text(root, "start_page"),
        "num_pages": _child_text(root, "num_pages"),
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
        if action_name == "read_pdf":
            start_page = int(action.get("start_page") or "1")
            num_pages = int(action.get("num_pages") or "1")
            observation = PaperPDFReadTool(config).read(
                paper,
                start_page=start_page,
                num_pages=num_pages,
            )
            return f"read_pdf(start_page={start_page}, num_pages={num_pages})\n{observation}", []
        if action_name == "search_scholar":
            query = action.get("query") or question
            papers = RetrievalTool(config).search(query, paper.get("metadata", {}))
            rendered = "\n".join(
                f"- {item.get('title')} ({item.get('year')}), citations={item.get('citation_count')}, url={item.get('url')}"
                for item in papers[:8]
            )
            return f"search_scholar({query!r})\n{rendered or 'No retrieved papers.'}", papers
    except Exception as exc:
        return f"{action_name} failed: {exc}", []
    return f"Unsupported action: {action_name}", []


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

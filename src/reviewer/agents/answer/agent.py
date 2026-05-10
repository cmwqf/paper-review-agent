"""Purpose: Answer Agent scaffold.

The Answer Agent answers one dimension-specific review question. Unlike a plain
answer model, it is allowed to decide whether it needs paper-local evidence,
external retrieval evidence, or both before writing the final QAResult.

Planned loop:

1. Observe question, dimension, paper map, and compact prior context.
2. Choose an action: search_file, read_file, search_scholar, or write_answer.
3. Use tools to gather evidence.
4. Write `<qa_result>` with answer, evidence summary, trace refs, and review impact.

Raw paper chunks and retrieval results should be stored in the full trace, not
blindly carried into the next Agent prompt.
"""

from __future__ import annotations

from reviewer.agents.base import BaseAgent
from reviewer.schemas.qa import QAResult


class AnswerAgent(BaseAgent):
    """Evidence-seeking agent that produces structured QAResult objects."""

    name = "answer"

    def run(self, question: str, dimension: str, paper: dict, paper_summary: dict | str) -> QAResult:
        """Answer one review question with evidence and review impact.

        This is a scaffold. The implementation will add an action loop and tool
        calls for paper_search, paper_read, and external retrieval.
        """
        raise NotImplementedError("AnswerAgent.run is scaffolded.")


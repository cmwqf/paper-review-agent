"""Purpose: Q&A tool used by dimension agents during their trajectories."""

from __future__ import annotations

from reviewer.schemas.qa import QAResult


class QATool:
    """Answer dimension-specific questions and attach review impact metadata."""

    def __init__(self, config: dict):
        self.config = config

    def ask(self, question: str, dimension: str, need_retrieval: bool) -> QAResult:
        """Answer one review question.

        The final implementation will optionally call retrieval and then the
        configured answer model.
        """
        raise NotImplementedError("QATool.ask is scaffolded.")


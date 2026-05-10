"""Purpose: Answer Agent schema aliases and future action schemas."""

from __future__ import annotations

from reviewer.schemas.qa import QAResult, ReviewImpact


class AnswerAgentResult(QAResult):
    """Final structured result produced by the Answer Agent."""


class AnswerAgentImpact(ReviewImpact):
    """Review impact schema specialized for Answer Agent output."""


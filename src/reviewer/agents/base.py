"""Purpose: Base interfaces and shared utilities for all agents."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentContext:
    """Common context passed to agents."""

    config: dict
    paper: dict
    summary_xml: str | None = None


class BaseAgent:
    """Minimal base class for future LLM-backed agents."""

    name: str = "base"

    def __init__(self, config: dict):
        self.config = config


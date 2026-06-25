"""Purpose: Base interfaces and shared utilities for all agents."""

from __future__ import annotations


class BaseAgent:
    """Minimal base class for future LLM-backed agents."""

    name: str = "base"

    def __init__(self, config: dict):
        self.config = config

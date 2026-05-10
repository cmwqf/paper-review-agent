"""Purpose: Represent and persist Q&A trajectories for each agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentTrace:
    """Append-only record of an agent's decisions, questions, and answers."""

    agent_name: str
    events: list[dict[str, Any]] = field(default_factory=list)

    def append(self, event: dict[str, Any]) -> None:
        """Add one trace event."""
        self.events.append(event)


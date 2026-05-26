"""Purpose: Shared workflow state passed between summary, dimension, and final agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReviewWorkflowState:
    """Container for intermediate and final artifacts of one paper review."""

    paper: dict[str, Any]
    summary_xml: str | None = None
    dimension_reviews: dict[str, str] = field(default_factory=dict)
    qa_trajectories: dict[str, list[Any]] = field(default_factory=dict)
    traces: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    final_review_xml: str | None = None

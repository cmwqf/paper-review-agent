"""Purpose: Presentation Agent logic, including optional VLM observations."""

from __future__ import annotations

from reviewer.agents.dimension_base import DimensionAgent
from reviewer.dimensions import ReviewDimension


class PresentationAgent(DimensionAgent):
    """Evaluate clarity, formatting, figures, tables, and readability."""

    name = "presentation"
    dimension = ReviewDimension.PRESENTATION


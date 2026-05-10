"""Purpose: Soundness Agent logic for technical reliability review."""

from __future__ import annotations

from reviewer.agents.dimension_base import DimensionAgent
from reviewer.dimensions import ReviewDimension


class SoundnessAgent(DimensionAgent):
    """Evaluate methodology, baselines, ablations, and evidence quality."""

    name = "soundness"
    dimension = ReviewDimension.SOUNDNESS


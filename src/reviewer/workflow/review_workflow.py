"""Purpose: High-level orchestration for the Reviewer pipeline."""

from __future__ import annotations

from reviewer.workflow.state import ReviewWorkflowState


class ReviewWorkflow:
    """Run Summary -> dimension agents -> Final Review for one paper."""

    def __init__(self, config: dict):
        self.config = config

    def run(self, paper: dict) -> ReviewWorkflowState:
        """Execute the scaffolded workflow.

        The concrete agent calls will be implemented after interfaces stabilize.
        """
        raise NotImplementedError("ReviewWorkflow.run is scaffolded.")


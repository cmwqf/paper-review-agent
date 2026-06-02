"""Purpose: High-level orchestration for the Reviewer pipeline."""

from __future__ import annotations

from collections.abc import Callable

from reviewer.agents.contribution.agent import ContributionAgent
from reviewer.agents.final.agent import FinalReviewAgent
from reviewer.agents.presentation.agent import PresentationAgent
from reviewer.agents.soundness.agent import SoundnessAgent
from reviewer.agents.summary.agent import SummaryAgent
from reviewer.workflow.state import ReviewWorkflowState


class ReviewWorkflow:
    """Run Summary -> dimension agents -> Final Review for one paper."""

    def __init__(self, config: dict):
        self.config = config

    def run(
        self,
        paper: dict,
        artifact_callback: Callable[[ReviewWorkflowState], None] | None = None,
    ) -> ReviewWorkflowState:
        """Execute Summary -> dimensions -> Final Review for one paper."""
        state = ReviewWorkflowState(paper=paper)
        summary_agent = SummaryAgent(self.config)
        state.summary_xml = summary_agent.run(paper)
        state.traces["summary"] = getattr(summary_agent, "trace_events", [])
        if artifact_callback:
            artifact_callback(state)

        dimension_agents = [
            ContributionAgent(self.config),
            SoundnessAgent(self.config),
            PresentationAgent(self.config),
        ]
        for agent in dimension_agents:
            review_xml, qa_results = agent.run_with_qa(paper, state.summary_xml)
            state.dimension_reviews[agent.dimension.value] = review_xml
            state.qa_trajectories[agent.dimension.value] = qa_results
            state.traces[f"{agent.dimension.value}.dimension_agent"] = getattr(
                agent, "trace_events", []
            )
            answer_events = []
            for result in qa_results:
                answer_events.extend(getattr(result, "trace_events", []))
            state.traces[f"{agent.dimension.value}.answer_agent"] = answer_events
            if artifact_callback:
                artifact_callback(state)

        final_agent = FinalReviewAgent(self.config)
        state.final_review_xml = final_agent.run(
            state.summary_xml,
            state.dimension_reviews,
        )
        state.traces["final_review"] = getattr(final_agent, "trace_events", [])
        if artifact_callback:
            artifact_callback(state)
        return state

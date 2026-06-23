"""Purpose: High-level orchestration for the Reviewer pipeline."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

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
        summary_xml: str | None = None,
    ) -> ReviewWorkflowState:
        """Execute Summary -> dimensions -> Final Review for one paper.

        If ``summary_xml`` is provided, it is reused as-is and the Summary stage
        is skipped (used by --reuse-from when 'summary' is not in --rerun-stages);
        otherwise the Summary agent generates it.
        """
        state = ReviewWorkflowState(paper=paper)
        if summary_xml:
            state.summary_xml = summary_xml
        else:
            summary_agent = SummaryAgent(self.config)
            state.summary_xml = summary_agent.run(paper)
            state.traces["summary"] = getattr(summary_agent, "trace_events", [])
        if artifact_callback:
            artifact_callback(state)

        dimension_agents = _dimension_agents(self.config)
        with ThreadPoolExecutor(max_workers=len(dimension_agents)) as executor:
            futures = {
                executor.submit(_run_dimension_agent, agent, paper, state.summary_xml): agent
                for agent in dimension_agents
            }
            for future in as_completed(futures):
                result = future.result()
                _record_dimension_result(state, result)
                if artifact_callback:
                    artifact_callback(state)

        _order_dimension_state(state)

        final_agent = FinalReviewAgent(self.config)
        state.final_review_xml = final_agent.run(
            state.summary_xml,
            state.dimension_reviews,
            state.qa_trajectories,
        )
        state.traces["final_review"] = getattr(final_agent, "trace_events", [])
        if artifact_callback:
            artifact_callback(state)
        return state


def _dimension_agents(config: dict):
    """Build the three independent dimension agents."""
    return [
        ContributionAgent(config),
        SoundnessAgent(config),
        PresentationAgent(config),
    ]


def _run_dimension_agent(agent, paper: dict, summary_xml: str) -> dict[str, Any]:
    """Run one dimension agent and collect trace payloads."""
    review_xml, qa_results = agent.run_with_qa(paper, summary_xml)
    dimension = agent.dimension.value
    answer_events = []
    for result in qa_results:
        answer_events.extend(getattr(result, "trace_events", []))
    return {
        "dimension": dimension,
        "review_xml": review_xml,
        "qa_results": qa_results,
        "dimension_events": getattr(agent, "trace_events", []),
        "answer_events": answer_events,
    }


def _record_dimension_result(state: ReviewWorkflowState, result: dict[str, Any]) -> None:
    """Merge one completed dimension result into workflow state."""
    dimension = result["dimension"]
    state.dimension_reviews[dimension] = result["review_xml"]
    state.qa_trajectories[dimension] = result["qa_results"]
    state.traces[f"{dimension}.dimension_agent"] = result["dimension_events"]
    state.traces[f"{dimension}.answer_agent"] = result["answer_events"]


def _order_dimension_state(state: ReviewWorkflowState) -> None:
    """Keep dimension mappings in canonical order after parallel completion."""
    order = ["Contribution", "Soundness", "Presentation"]
    state.dimension_reviews = {
        dimension: state.dimension_reviews[dimension]
        for dimension in order
        if dimension in state.dimension_reviews
    }
    state.qa_trajectories = {
        dimension: state.qa_trajectories[dimension]
        for dimension in order
        if dimension in state.qa_trajectories
    }
    ordered_traces = {}
    if "summary" in state.traces:
        ordered_traces["summary"] = state.traces["summary"]
    for dimension in order:
        for suffix in ["dimension_agent", "answer_agent"]:
            key = f"{dimension}.{suffix}"
            if key in state.traces:
                ordered_traces[key] = state.traces[key]
    for key, value in state.traces.items():
        if key not in ordered_traces:
            ordered_traces[key] = value
    state.traces = ordered_traces

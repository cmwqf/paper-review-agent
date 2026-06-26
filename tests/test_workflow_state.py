"""Purpose: Tests for workflow state containers."""

from threading import Barrier, Lock

from reviewer.dimensions import ReviewDimension
from reviewer.schemas.qa import QAResult, ReviewImpact
from reviewer.workflow.review_workflow import ReviewWorkflow
from reviewer.workflow.state import ReviewWorkflowState


def test_workflow_state_defaults() -> None:
    """State should initialize trace and review mappings."""
    state = ReviewWorkflowState(paper={"path": "paper.pdf"})
    assert state.dimension_reviews == {}
    assert state.qa_trajectories == {}
    assert state.traces == {}


def test_review_workflow_calls_artifact_callback_after_each_stage(monkeypatch) -> None:
    """Workflow should allow artifacts to be persisted incrementally."""

    class FakeSummaryAgent:
        def __init__(self, config):
            self.trace_events = [{"event": "summary"}]

        def run(self, paper):
            return "<paper_summary><metadata><title>Paper</title></metadata></paper_summary>"

    class FakeDimensionAgent:
        def __init__(self, config, dimension):
            self.dimension = dimension
            self.trace_events = [{"event": f"{dimension.value}.dimension"}]

        def run_with_qa(self, paper, summary_xml, preloaded_qa_results=None, on_qa_result=None):
            qa = QAResult(
                question=f"{self.dimension.value} question",
                answer="answer",
                evidence=["paper"],
                review_impact=ReviewImpact(
                    dimension=self.dimension.value,
                    polarity="strength",
                    impact_level="C1",
                    confidence="medium",
                ),
            )
            if on_qa_result is not None:
                on_qa_result(qa)
            return (
                f"<dimension_review><dimension>{self.dimension.value}</dimension></dimension_review>",
                [qa],
            )

    class FakeFinalAgent:
        def __init__(self, config):
            self.trace_events = [{"event": "final"}]

        def run(self, summary_xml, dimension_reviews, qa_trajectories=None):
            return "<final_review><summary>done</summary></final_review>"

    monkeypatch.setattr("reviewer.workflow.review_workflow.SummaryAgent", FakeSummaryAgent)
    monkeypatch.setattr(
        "reviewer.workflow.review_workflow.ContributionAgent",
        lambda config: FakeDimensionAgent(config, ReviewDimension.CONTRIBUTION),
    )
    monkeypatch.setattr(
        "reviewer.workflow.review_workflow.SoundnessAgent",
        lambda config: FakeDimensionAgent(config, ReviewDimension.SOUNDNESS),
    )
    monkeypatch.setattr(
        "reviewer.workflow.review_workflow.PresentationAgent",
        lambda config: FakeDimensionAgent(config, ReviewDimension.PRESENTATION),
    )
    monkeypatch.setattr("reviewer.workflow.review_workflow.FinalReviewAgent", FakeFinalAgent)

    snapshots = []
    ReviewWorkflow({}).run(
        {"id": "paper"},
        artifact_callback=lambda state: snapshots.append(
            (
                bool(state.summary_xml),
                tuple(state.dimension_reviews),
                bool(state.final_review_xml),
            )
        ),
    )

    assert len(snapshots) == 5
    assert snapshots[0] == (True, (), False)
    assert snapshots[-1] == (
        True,
        ("Contribution", "Soundness", "Presentation"),
        True,
    )
    dimension_snapshots = snapshots[1:4]
    assert [len(snapshot[1]) for snapshot in dimension_snapshots] == [1, 2, 3]
    assert set(dimension_snapshots[-1][1]) == {"Contribution", "Soundness", "Presentation"}


def test_review_workflow_runs_dimensions_concurrently(monkeypatch) -> None:
    """The three dimension agents should run in parallel after summary generation."""

    class FakeSummaryAgent:
        def __init__(self, config):
            self.trace_events = [{"event": "summary"}]

        def run(self, paper):
            return "<paper_summary><metadata><title>Paper</title></metadata></paper_summary>"

    class FakeDimensionAgent:
        active = 0
        max_active = 0
        lock = Lock()
        barrier = Barrier(3)

        def __init__(self, config, dimension):
            self.dimension = dimension
            self.trace_events = [{"event": f"{dimension.value}.dimension"}]

        def run_with_qa(self, paper, summary_xml, preloaded_qa_results=None, on_qa_result=None):
            with self.lock:
                type(self).active += 1
                type(self).max_active = max(type(self).max_active, type(self).active)
            try:
                type(self).barrier.wait(timeout=2)
                qa = QAResult(
                    question=f"{self.dimension.value} question",
                    answer="answer",
                    evidence=["paper"],
                    review_impact=ReviewImpact(
                        dimension=self.dimension.value,
                        polarity="strength",
                        impact_level="C1",
                        confidence="medium",
                    ),
                )
                return (
                    f"<dimension_review><dimension>{self.dimension.value}</dimension></dimension_review>",
                    [qa],
                )
            finally:
                with self.lock:
                    type(self).active -= 1

    class FakeFinalAgent:
        def __init__(self, config):
            self.trace_events = [{"event": "final"}]

        def run(self, summary_xml, dimension_reviews, qa_trajectories=None):
            return "<final_review><summary>done</summary></final_review>"

    monkeypatch.setattr("reviewer.workflow.review_workflow.SummaryAgent", FakeSummaryAgent)
    monkeypatch.setattr(
        "reviewer.workflow.review_workflow.ContributionAgent",
        lambda config: FakeDimensionAgent(config, ReviewDimension.CONTRIBUTION),
    )
    monkeypatch.setattr(
        "reviewer.workflow.review_workflow.SoundnessAgent",
        lambda config: FakeDimensionAgent(config, ReviewDimension.SOUNDNESS),
    )
    monkeypatch.setattr(
        "reviewer.workflow.review_workflow.PresentationAgent",
        lambda config: FakeDimensionAgent(config, ReviewDimension.PRESENTATION),
    )
    monkeypatch.setattr("reviewer.workflow.review_workflow.FinalReviewAgent", FakeFinalAgent)

    state = ReviewWorkflow({}).run({"id": "paper"})

    assert FakeDimensionAgent.max_active == 3
    assert tuple(state.dimension_reviews) == ("Contribution", "Soundness", "Presentation")

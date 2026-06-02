"""Purpose: Tests for workflow state containers."""

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

        def run_with_qa(self, paper, summary_xml):
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

    class FakeFinalAgent:
        def __init__(self, config):
            self.trace_events = [{"event": "final"}]

        def run(self, summary_xml, dimension_reviews):
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

    assert snapshots == [
        (True, (), False),
        (True, ("Contribution",), False),
        (True, ("Contribution", "Soundness"), False),
        (True, ("Contribution", "Soundness", "Presentation"), False),
        (True, ("Contribution", "Soundness", "Presentation"), True),
    ]

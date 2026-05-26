"""Purpose: Tests for workflow state containers."""

from reviewer.workflow.state import ReviewWorkflowState


def test_workflow_state_defaults() -> None:
    """State should initialize trace and review mappings."""
    state = ReviewWorkflowState(paper={"path": "paper.pdf"})
    assert state.dimension_reviews == {}
    assert state.qa_trajectories == {}
    assert state.traces == {}

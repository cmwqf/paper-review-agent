"""Purpose: Tests for prompt loading helpers."""

from __future__ import annotations

from reviewer.utils.prompts import join_prompts, load_prompt, load_rubric_prompt


def test_load_prompt_from_repo_root() -> None:
    """Prompt loader should resolve repo-relative prompt paths."""
    prompt = load_prompt("prompts/summary_agent_system.md")
    assert "Summary Agent" in prompt


def test_join_prompts_preserves_order() -> None:
    """Prompt joining should preserve caller-specified order."""
    prompt = join_prompts(["prompts/summary_agent_system.md", "prompts/summary_agent_output_contract.md"])
    assert prompt.index("Summary Agent") < prompt.index("paper_summary")


def test_load_rubric_prompt_defaults_to_iclr() -> None:
    """Rubric loader should use ICLR as the default active profile."""
    prompt = load_rubric_prompt({})
    assert "Active review rubric profile: ICLR" in prompt
    assert "Contribution evaluates" in prompt


def test_dimension_review_writer_prompts_load() -> None:
    """Dimension review writer guidance should be split by dimension."""
    contribution = load_prompt("prompts/contribution_review_writer_guidance.md")
    soundness = load_prompt("prompts/soundness_review_writer_guidance.md")
    presentation = load_prompt("prompts/presentation_review_writer_guidance.md")

    assert "final Contribution dimension review" in contribution
    assert "novelty and originality" in contribution
    assert "final Soundness dimension review" in soundness
    assert "central claims" in soundness
    assert "final Presentation dimension review" in presentation
    assert "read, navigate, inspect, and verify" in presentation

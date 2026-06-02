"""Purpose: Tests for prompt loading helpers."""

from __future__ import annotations

from reviewer.utils.prompts import join_prompts, load_prompt, load_rubric_prompt


def test_load_prompt_from_repo_root() -> None:
    """Prompt loader should resolve repo-relative prompt paths."""
    prompt = load_prompt("prompts/summary_system.md")
    assert "Summary Agent" in prompt


def test_join_prompts_preserves_order() -> None:
    """Prompt joining should preserve caller-specified order."""
    prompt = join_prompts(["prompts/summary_system.md", "prompts/summary_output_xml.md"])
    assert prompt.index("Summary Agent") < prompt.index("paper_summary")


def test_load_rubric_prompt_defaults_to_iclr() -> None:
    """Rubric loader should use ICLR as the default active profile."""
    prompt = load_rubric_prompt({})
    assert "Active review rubric profile: ICLR" in prompt
    assert "Contribution evaluates" in prompt

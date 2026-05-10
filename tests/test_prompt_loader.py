"""Purpose: Tests for prompt loading helpers."""

from __future__ import annotations

from reviewer.utils.prompts import join_prompts, load_prompt


def test_load_prompt_from_repo_root() -> None:
    """Prompt loader should resolve repo-relative prompt paths."""
    prompt = load_prompt("prompts/summary_system.md")
    assert "Summary Agent" in prompt


def test_join_prompts_preserves_order() -> None:
    """Prompt joining should preserve caller-specified order."""
    prompt = join_prompts(["prompts/summary_system.md", "prompts/summary_output_xml.md"])
    assert prompt.index("Summary Agent") < prompt.index("paper_summary")

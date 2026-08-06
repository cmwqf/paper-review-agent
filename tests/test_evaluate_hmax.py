"""Purpose: Tests for H-Max evaluation helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_evaluate_hmax():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_hmax.py"
    spec = importlib.util.spec_from_file_location("evaluate_hmax", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_hmax_prompt_requires_human_issue_consistency_check():
    evaluate_hmax = load_evaluate_hmax()

    prompt = evaluate_hmax.scholarpeer_hmax_system_prompt("2024-01-01")
    prompt_lower = prompt.lower()

    assert "human-review issue consistency" in prompt_lower
    assert "unsupported/resolved human-review issues must not make the best-human baseline stronger" in prompt_lower
    assert "Consistency-Adjusted Best Human Baseline" in prompt
    assert "Human Review Issue Consistency Findings" in prompt


def test_normalize_evaluation_preserves_human_issue_consistency_fields():
    evaluate_hmax = load_evaluate_hmax()
    parsed = {
        "Human Review Issue Consistency Findings": [
            {
                "human_review_id": "human_0",
                "issue": "missing ablation",
                "status": "unsupported/resolved",
                "paper_evidence": "Table 3 reports the ablation.",
                "scoring_effect": "Do not penalize the AI for omitting this issue.",
            }
        ],
        "Human Review Issue Consistency Reason": "The ablation complaint is resolved.",
        "Technical Accuracy Reason": "Accurate.",
        "Technical Accuracy Score": 6,
        "Constructive Value Reason": "Useful.",
        "Constructive Value Score": 6,
        "Analytical Depth Reason": "Detailed.",
        "Analytical Depth Score": 6,
        "Novelty and Significance Assessment Reason": "Grounded.",
        "Novelty and Significance Assessment Score": 5,
        "Overall Reason": "Slightly stronger than baseline.",
        "Overall Score": 6,
    }
    job = {"paper_id": "paper1", "title": "Paper", "cutoff_date": "2024-01-01", "human_reviews": [{}]}

    row = evaluate_hmax.normalize_evaluation(job, parsed, "raw")

    assert row["Human Review Issue Consistency Findings"] == parsed[
        "Human Review Issue Consistency Findings"
    ]
    assert row["Human Review Issue Consistency Reason"] == "The ablation complaint is resolved."
    assert row["Overall Score"] == 6

"""Purpose: Tests for DeepReview-13K and text paper loading."""

from __future__ import annotations

import json

from reviewer.paper.loader import load_paper


def test_load_deepreview_jsonl_row(tmp_path) -> None:
    """DeepReview-13K JSONL rows should normalize to paper dicts."""
    path = tmp_path / "sample.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "abc",
                "title": "A Paper",
                "paper_context": "body",
                "date": "2024-01-01",
                "year": 2024,
                "decision": "Accept",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    paper = load_paper(path)
    assert paper["id"] == "abc"
    assert paper["text"] == "body"
    assert paper["metadata"]["submission_date"] == "2024-01-01"


def test_load_text_paper(tmp_path) -> None:
    """Plain text files should also be supported for small manual tests."""
    path = tmp_path / "paper.txt"
    path.write_text("hello", encoding="utf-8")
    paper = load_paper(path)
    assert paper["id"] == "paper"
    assert paper["text"] == "hello"

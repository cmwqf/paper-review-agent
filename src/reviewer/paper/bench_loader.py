"""Purpose: Load DeepReview-Bench split rows into Reviewer paper dictionaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_bench_split(path: str | Path) -> list[dict[str, Any]]:
    """Load a DeepReview-Bench split JSONL file."""
    split_path = Path(path)
    rows: list[dict[str, Any]] = []
    with split_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_bench_paper(row: dict[str, Any], bench_root: str | Path) -> dict[str, Any]:
    """Load one DeepReview-Bench paper from a split row."""
    paper_id = str(row.get("id") or "").strip()
    if not paper_id:
        raise ValueError("DeepReview-Bench row must contain an id.")
    paper_dir = Path(bench_root) / "papers" / paper_id
    metadata_path = paper_dir / "metadata.json"
    markdown_path = paper_dir / "paper.md"
    pdf_path = paper_dir / "paper.pdf"
    review_path = paper_dir / "review.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing metadata.json for {paper_id}: {metadata_path}")
    if not markdown_path.exists():
        raise FileNotFoundError(f"Missing paper.md for {paper_id}: {markdown_path}")
    if not pdf_path.exists():
        raise FileNotFoundError(f"Missing paper.pdf for {paper_id}: {pdf_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    title = metadata.get("title") or row.get("title") or paper_id
    paper = {
        "id": paper_id,
        "title": title,
        "text": markdown_path.read_text(encoding="utf-8"),
        "metadata": {
            "id": paper_id,
            "title": title,
            "source": "DeepReview-Bench",
            "source_path": str(pdf_path),
            "markdown_path": str(markdown_path),
            "metadata_path": str(metadata_path),
            "review_path": str(review_path) if review_path.exists() else None,
            "submission_date": metadata.get("date") or row.get("date"),
            "date": metadata.get("date") or row.get("date"),
            "venue": metadata.get("venue") or row.get("venue"),
            "venue_year": metadata.get("venue_year") or row.get("venue_year"),
            "decision": metadata.get("decision") or row.get("decision"),
            "openreview_pdf_url": metadata.get("openreview_pdf_url"),
            "split_source_file": row.get("source_file"),
            "split_source_index": row.get("source_index"),
        },
        "raw": {},
    }
    paper["raw"] = {
        "split_row": row,
        "metadata": metadata,
    }
    return paper

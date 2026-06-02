"""Purpose: Load DeepReview-Bench split rows into Reviewer paper dictionaries."""

from __future__ import annotations

import json
import re
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
    figures_dir = paper_dir / "figures"
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
            "figures_dir": str(figures_dir) if figures_dir.exists() else None,
            "submission_date": metadata.get("date") or row.get("date"),
            "date": metadata.get("date") or row.get("date"),
            "venue": metadata.get("venue") or row.get("venue"),
            "venue_year": metadata.get("venue_year") or row.get("venue_year"),
            "decision": metadata.get("decision") or row.get("decision"),
            "openreview_pdf_url": metadata.get("openreview_pdf_url"),
            "split_source_file": row.get("source_file"),
            "split_source_index": row.get("source_index"),
        },
        "figures": _load_figure_assets(figures_dir),
        "raw": {},
    }
    paper["raw"] = {
        "split_row": row,
        "metadata": metadata,
    }
    return paper


def _load_figure_assets(figures_dir: Path) -> list[dict[str, Any]]:
    """Load extracted DeepReview-Bench figure assets."""
    if not figures_dir.exists():
        return []
    assets: list[dict[str, Any]] = []
    for image_path in sorted(figures_dir.glob("*.jpeg")):
        parsed = _parse_figure_asset_name(image_path)
        if parsed:
            assets.append(parsed)
    return assets


def _parse_figure_asset_name(image_path: Path) -> dict[str, Any] | None:
    """Parse filenames like _page_4_Figure_2.jpeg into a figure asset record."""
    match = re.match(
        r"^_page_(?P<page_index>\d+)_(?P<kind>Figure|Picture)_(?P<number>[A-Za-z0-9.]+)\.jpeg$",
        image_path.name,
    )
    if not match:
        return None
    page_index = int(match.group("page_index"))
    kind = match.group("kind")
    number = match.group("number")
    label = f"{kind} {number}"
    return {
        "label": label,
        "kind": kind,
        "number": number,
        "path": str(image_path),
        "filename": image_path.name,
        "page_index": page_index,
        "pdf_page": page_index + 1,
    }

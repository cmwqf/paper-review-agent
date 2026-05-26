"""Purpose: Load papers from PDF, text, JSON, or DeepReview-13K JSONL rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reviewer.paper.text_extractor import extract_pdf_pages


def paper_from_deepreview_row(row: dict[str, Any], source_path: str | Path, index: int) -> dict[str, Any]:
    """Normalize one DeepReview-13K JSONL row into the internal paper format."""
    paper_id = str(row.get("id") or f"{Path(source_path).stem}-{index}")
    metadata = {
        "id": paper_id,
        "title": row.get("title"),
        "submission_date": row.get("date"),
        "year": row.get("year"),
        "decision": row.get("decision"),
        "source": "DeepReview-13K",
        "source_path": str(source_path),
        "source_index": index,
    }
    text = str(row.get("paper_context") or row.get("text") or row.get("abstract") or "")
    return {
        "id": paper_id,
        "title": row.get("title") or paper_id,
        "text": text,
        "metadata": metadata,
        "raw": row,
    }


def load_jsonl_row(path: str | Path, index: int = 0) -> dict[str, Any]:
    """Load one row from a JSONL file by zero-based index."""
    paper_path = Path(path)
    if index < 0:
        raise ValueError("JSONL index must be non-negative.")
    with paper_path.open("r", encoding="utf-8") as handle:
        for line_index, line in enumerate(handle):
            if line_index == index:
                row = json.loads(line)
                return paper_from_deepreview_row(row, paper_path, index)
    raise IndexError(f"JSONL index {index} is out of range for {paper_path}.")


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON paper descriptor or a DeepReview-style row."""
    paper_path = Path(path)
    row = json.loads(paper_path.read_text(encoding="utf-8"))
    if isinstance(row, list):
        if not row:
            raise ValueError(f"JSON file contains an empty list: {paper_path}")
        row = row[0]
    if not isinstance(row, dict):
        raise ValueError(f"JSON paper input must be an object or list of objects: {paper_path}")
    return paper_from_deepreview_row(row, paper_path, 0)


def load_text(path: str | Path) -> dict[str, Any]:
    """Load a plain-text paper into the internal paper format."""
    paper_path = Path(path)
    text = paper_path.read_text(encoding="utf-8")
    paper_id = paper_path.stem
    return {
        "id": paper_id,
        "title": paper_id,
        "text": text,
        "metadata": {
            "id": paper_id,
            "title": paper_id,
            "source": "text",
            "source_path": str(paper_path),
        },
        "raw": {},
    }


def load_pdf(path: str | Path) -> dict[str, Any]:
    """Load a PDF paper by extracting page-level text."""
    paper_path = Path(path)
    pages = extract_pdf_pages(paper_path)
    paper_id = paper_path.stem
    text = "\n\n".join(
        f"=== Page {page_index} ===\n{page_text}"
        for page_index, page_text in enumerate(pages, start=1)
    )
    return {
        "id": paper_id,
        "title": paper_id,
        "text": text,
        "pdf_pages": pages,
        "metadata": {
            "id": paper_id,
            "title": paper_id,
            "source": "pdf",
            "source_path": str(paper_path),
            "page_count": len(pages),
        },
        "raw": {},
    }


def load_paper(path: str | Path, *, index: int = 0) -> dict[str, Any]:
    """Load a paper path into a normalized paper dictionary."""
    paper_path = Path(path)
    suffix = paper_path.suffix.lower()
    if suffix == ".jsonl":
        return load_jsonl_row(paper_path, index=index)
    if suffix == ".json":
        return load_json(paper_path)
    if suffix in {".txt", ".md", ".tex"}:
        return load_text(paper_path)
    if suffix == ".pdf":
        return load_pdf(paper_path)
    raise ValueError(f"Unsupported paper input type: {paper_path}")

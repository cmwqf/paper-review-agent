"""Purpose: Read page-level PDF text evidence for presentation review."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reviewer.paper.text_extractor import extract_pdf_pages


@dataclass
class PDFReadResult:
    """Page-level PDF text returned by PaperPDFReadTool."""

    ref_id: str
    start_page: int
    end_page: int
    text: str


class PaperPDFReadTool:
    """Read extracted PDF text by page range."""

    def __init__(self, config: dict):
        self.config = config

    def read_result(self, paper: dict, start_page: int = 1, num_pages: int = 1) -> PDFReadResult:
        """Return extracted text for a bounded 1-based page range."""
        if start_page < 1:
            raise ValueError("start_page must be >= 1.")
        if num_pages < 1:
            raise ValueError("num_pages must be >= 1.")
        max_pages = int(self.config.get("paper", {}).get("max_pdf_read_pages", 3))
        if num_pages > max_pages:
            raise ValueError(f"num_pages must be <= {max_pages}.")

        pages = _paper_pdf_pages(paper)
        if not pages:
            raise ValueError("No PDF pages are available for this paper.")
        if start_page > len(pages):
            raise ValueError(f"start_page {start_page} exceeds PDF page count {len(pages)}.")
        end_page = min(len(pages), start_page + num_pages - 1)
        selected = pages[start_page - 1 : end_page]
        text = "\n\n".join(
            f"Page {page_number}:\n{page_text}"
            for page_number, page_text in enumerate(selected, start=start_page)
        )
        return PDFReadResult(
            ref_id=f"P{start_page}-P{end_page}",
            start_page=start_page,
            end_page=end_page,
            text=text,
        )

    def read(self, paper: dict, start_page: int = 1, num_pages: int = 1) -> str:
        """Return text meant for model observation."""
        return self.read_result(paper, start_page=start_page, num_pages=num_pages).text


def _paper_pdf_pages(paper: dict) -> list[str]:
    """Resolve page text from loaded paper data or source PDF path."""
    pages = paper.get("pdf_pages")
    if isinstance(pages, list):
        return [str(page) for page in pages]

    source_path = paper.get("metadata", {}).get("source_path")
    if source_path and Path(source_path).suffix.lower() == ".pdf":
        return extract_pdf_pages(source_path)
    return []

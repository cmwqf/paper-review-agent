"""Purpose: Extract paper text from PDF or text files for LLM context."""

from __future__ import annotations

from pathlib import Path


def extract_pdf_pages(path: str | Path, max_chars_per_page: int | None = None) -> list[str]:
    """Extract text from each PDF page using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on optional runtime install
        raise RuntimeError("PDF text extraction requires the 'pypdf' package.") from exc

    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.strip()
        if max_chars_per_page is not None:
            text = text[:max_chars_per_page]
        pages.append(text)
    if not any(page.strip() for page in pages):
        raise ValueError(f"No extractable text found in PDF: {path}")
    return pages


def extract_text(path: str | Path, max_chars: int | None = None) -> str:
    """Extract text from a PDF or plain text file."""
    paper_path = Path(path)
    if paper_path.suffix.lower() == ".pdf":
        pages = extract_pdf_pages(paper_path)
        text = "\n\n".join(
            f"=== Page {page_index} ===\n{page_text}"
            for page_index, page_text in enumerate(pages, start=1)
        )
    else:
        text = paper_path.read_text(encoding="utf-8")
    return text[:max_chars] if max_chars else text

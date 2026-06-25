"""Purpose: Render PDF pages as images for VLM-based presentation review."""

from __future__ import annotations

from pathlib import Path


def render_pdf_page_range(
    pdf_path: str | Path,
    output_dir: str | Path,
    start_page: int,
    num_pages: int,
    dpi: int = 160,
) -> list[str]:
    """Render a bounded 1-based PDF page range to PNG images."""
    if start_page < 1:
        raise ValueError("start_page must be >= 1.")
    if num_pages < 1:
        return []
    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - depends on runtime install
        raise RuntimeError("PDF page rendering requires the 'PyMuPDF' package.") from exc

    pdf = fitz.open(str(pdf_path))
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    rendered: list[str] = []
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    try:
        if start_page > pdf.page_count:
            raise ValueError(f"start_page {start_page} exceeds PDF page count {pdf.page_count}.")
        start_index = start_page - 1
        end_index = min(pdf.page_count, start_index + num_pages)
        for page_index in range(start_index, end_index):
            page = pdf.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_path = output_path / f"page_{page_index + 1}.png"
            pixmap.save(str(image_path))
            rendered.append(str(image_path))
    finally:
        pdf.close()
    return rendered

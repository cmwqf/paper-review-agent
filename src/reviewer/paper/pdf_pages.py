"""Purpose: Render PDF pages as images for VLM-based presentation review."""

from __future__ import annotations

from pathlib import Path


def render_pdf_pages(pdf_path: str | Path, output_dir: str | Path, max_pages: int, dpi: int = 160) -> list[str]:
    """Render up to max_pages PDF pages to PNG images."""
    if max_pages < 1:
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
        for page_index in range(min(max_pages, pdf.page_count)):
            page = pdf.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_path = output_path / f"page_{page_index + 1}.png"
            pixmap.save(str(image_path))
            rendered.append(str(image_path))
    finally:
        pdf.close()
    return rendered

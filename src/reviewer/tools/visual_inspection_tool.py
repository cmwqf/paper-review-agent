"""Purpose: Unified visual inspection tool for figures, tables, and pages."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from reviewer.paper.pdf_pages import render_pdf_page_range
from reviewer.paper.text_extractor import extract_pdf_pages
from reviewer.tools.vlm_tool import VLMTool


class VisualInspectionTool:
    """Route one visual target to exactly one VLM image input."""

    def __init__(self, config: dict):
        self.config = config

    def inspect(self, paper: dict, target: str, focus: str = "") -> str:
        """Inspect one figure asset, table page, or PDF page."""
        if not self.config.get("agents", {}).get("presentation", {}).get("use_vlm", False):
            raise ValueError("Visual inspection is disabled by agents.presentation.use_vlm.")
        target = target.strip()
        if not target:
            raise ValueError("inspect_visual requires a target such as Figure 2, Table 1, or page 4.")

        route = self._route(paper, target, focus)
        observation = VLMTool(self.config).inspect_pages(
            [route["image_path"]],
            _visual_questions(target, focus, route),
        )
        return _format_observation(target, focus, route, observation)

    def _route(self, paper: dict, target: str, focus: str) -> dict[str, Any]:
        """Choose one image source for the visual target."""
        page_number = _parse_page_target(target)
        if page_number is not None:
            return self._render_pdf_page(paper, page_number, reason="explicit_page")

        figure_label = _parse_labeled_target(target, {"figure", "fig", "picture"})
        if figure_label:
            asset = _find_figure_asset(paper.get("figures", []), figure_label)
            if not asset:
                raise ValueError(_missing_figure_message(figure_label, paper.get("figures", [])))
            if _wants_page_layout(target, focus):
                return self._render_pdf_page(
                    paper,
                    int(asset["pdf_page"]),
                    reason="figure_page_layout",
                    label=asset["label"],
                    asset_path=asset["path"],
                )
            return {
                "kind": "figure_asset",
                "label": asset["label"],
                "image_path": asset["path"],
                "pdf_page": asset.get("pdf_page"),
                "reason": "figure_content",
            }

        table_label = _parse_labeled_target(target, {"table", "tab"})
        if table_label:
            page = _locate_label_page_in_pdf(paper, table_label)
            if page is None:
                raise ValueError(
                    f"{table_label} could not be located in PDF text. "
                    "Use search_file/read_file for table content and specify page N if visual layout is needed."
                )
            return self._render_pdf_page(paper, page, reason="table_page_layout", label=table_label)

        raise ValueError(
            "inspect_visual requires one specific visual target: Figure N, Picture N, Table N, or page N."
        )

    def _render_pdf_page(
        self,
        paper: dict,
        page_number: int,
        *,
        reason: str,
        label: str = "",
        asset_path: str = "",
    ) -> dict[str, Any]:
        """Render exactly one 1-based PDF page and return its image path."""
        source_path = paper.get("metadata", {}).get("source_path")
        if not source_path or Path(source_path).suffix.lower() != ".pdf":
            raise ValueError("No PDF source_path is available for visual inspection.")
        dpi = int(self.config.get("paper", {}).get("page_image_dpi", 220))
        output_dir = (
            Path(self.config.get("project", {}).get("output_dir", "outputs"))
            / "vlm_pages"
            / str(paper.get("id") or Path(source_path).stem)
            / f"page_{page_number}"
        )
        image_paths = render_pdf_page_range(
            source_path,
            output_dir,
            start_page=page_number,
            num_pages=1,
            dpi=dpi,
        )
        return {
            "kind": "pdf_page",
            "label": label,
            "image_path": image_paths[0],
            "pdf_page": page_number,
            "reason": reason,
            "asset_path": asset_path,
        }


def _parse_page_target(target: str) -> int | None:
    """Parse page targets such as page 4 or p. 4."""
    match = re.fullmatch(r"\s*(?:page|p\.?)\s*(\d+)\s*", target, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _parse_labeled_target(target: str, kinds: set[str]) -> str:
    """Parse labeled targets such as Figure 2 or Table 1."""
    kind_pattern = "|".join(re.escape(kind) for kind in sorted(kinds, key=len, reverse=True))
    pattern = r"\b(?P<kind>" + kind_pattern + r")\.?\s*(?P<number>[A-Za-z0-9.]+)\b"
    match = re.search(pattern, target, flags=re.IGNORECASE)
    if not match:
        return ""
    kind = match.group("kind").lower()
    canonical = "Figure" if kind in {"figure", "fig"} else "Picture" if kind == "picture" else "Table"
    return f"{canonical} {match.group('number')}"


def _find_figure_asset(assets: list[dict[str, Any]], label: str) -> dict[str, Any] | None:
    """Find an exact figure/picture asset by label."""
    target_kind, target_number = _split_label(label)
    for asset in assets:
        kind, number = _split_label(str(asset.get("label", "")))
        if kind == target_kind and number == target_number:
            return asset
    return None


def _split_label(label: str) -> tuple[str, str]:
    """Normalize a visual label for exact matching."""
    parts = label.strip().lower().replace("fig.", "figure").replace("tab.", "table").split(maxsplit=1)
    if len(parts) != 2:
        return "", ""
    return parts[0], parts[1].rstrip(".")


def _wants_page_layout(target: str, focus: str) -> bool:
    """Return whether the request is about page-level visual placement."""
    text = f"{target} {focus}".lower()
    return any(
        phrase in text
        for phrase in (
            "page layout",
            "layout",
            "placement",
            "on page",
            "caption crowd",
            "caption placement",
            "too small on the page",
            "surrounding",
            "page-level",
        )
    )


def _locate_label_page_in_pdf(paper: dict, label: str) -> int | None:
    """Locate the first PDF page containing a caption-like table label."""
    source_path = paper.get("metadata", {}).get("source_path")
    if not source_path:
        return None
    pages = paper.get("pdf_pages")
    if not isinstance(pages, list):
        try:
            pages = extract_pdf_pages(source_path)
        except Exception:
            return None
    kind, number = _split_label(label)
    if not kind or not number:
        return None
    pattern = re.compile(rf"\b{re.escape(kind)}\s*{re.escape(number)}(?![A-Za-z0-9.])", re.IGNORECASE)
    for index, page_text in enumerate(pages, start=1):
        if pattern.search(str(page_text)):
            return index
    return None


def _visual_questions(target: str, focus: str, route: dict[str, Any]) -> list[str]:
    """Build focused VLM questions for the chosen visual input."""
    focus_text = focus.strip() or (
        "Check presentation quality: readability of labels, legends, axes, captions, visual density, "
        "alignment, truncation, overlap, and whether the visual can be inspected clearly."
    )
    source_note = (
        f"The attached image is an extracted figure asset for {route.get('label') or target}."
        if route["kind"] == "figure_asset"
        else f"The attached image is exactly one rendered PDF page: page {route.get('pdf_page')}."
    )
    return [
        source_note,
        f"Target: {target}. Focus: {focus_text}",
        "Report only confirmed visual evidence. Separate evidence limitations from presentation weaknesses.",
    ]


def _format_observation(target: str, focus: str, route: dict[str, Any], observation: str) -> str:
    """Format VLM output for the AnswerAgent trace."""
    lines = [
        f"inspect_visual(target={target!r}, focus={focus!r})",
        "Visual input used:",
        f"- kind: {route['kind']}",
        f"- image_path: {route['image_path']}",
    ]
    if route.get("label"):
        lines.append(f"- label: {route['label']}")
    if route.get("pdf_page"):
        lines.append(f"- pdf_page: {route['pdf_page']}")
    if route.get("reason"):
        lines.append(f"- route_reason: {route['reason']}")
    lines.append("\nVLM observation:\n" + observation)
    return "\n".join(lines)


def _missing_figure_message(label: str, assets: list[dict[str, Any]]) -> str:
    """Return helpful feedback when a requested figure asset is absent."""
    candidates = ", ".join(
        f"{asset.get('label')} page {asset.get('pdf_page')}" for asset in assets[:12]
    )
    if not candidates:
        candidates = "no extracted figure assets available"
    return f"{label} not found in extracted figure assets. Available assets: {candidates}."

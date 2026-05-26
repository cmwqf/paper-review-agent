"""Purpose: Presentation Agent logic, including optional VLM observations."""

from __future__ import annotations

from pathlib import Path

from reviewer.agents.dimension_base import DimensionAgent
from reviewer.dimensions import ReviewDimension
from reviewer.paper.pdf_pages import render_pdf_pages
from reviewer.schemas.qa import QAResult, ReviewImpact
from reviewer.tools.vlm_tool import VLMTool


class PresentationAgent(DimensionAgent):
    """Evaluate clarity, formatting, figures, tables, and readability."""

    name = "presentation"
    dimension = ReviewDimension.PRESENTATION

    def initial_qa_results(self, paper: dict, summary_xml: str) -> list[QAResult]:
        """Preload PDF/VLM evidence so presentation review is PDF-grounded."""
        _ = summary_xml
        require_pdf = self.config.get("agents", {}).get("presentation", {}).get("require_pdf", True)
        observations: list[str] = []
        evidence_refs: list[str] = []

        vlm_observation = self._inspect_pdf_pages_with_vlm(paper)
        if vlm_observation:
            observations.append("VLM page observations:\n" + vlm_observation)
            evidence_refs.append("pdf_image:vlm_pages")

        if not observations:
            if require_pdf:
                raise ValueError(
                    "Presentation review requires PDF evidence. Provide a PDF source path, "
                    "enable VLM inspection, or provide paper['pdf_pages']; set "
                    "agents.presentation.require_pdf=false to allow fallback."
                )
            return []
        answer = "\n\n".join(observations)
        return [
            QAResult(
                question=(
                    "Inspect the PDF pages for presentation evidence: readability, "
                    "figures, tables, captions, layout, and formatting."
                ),
                answer=answer,
                evidence=evidence_refs,
                review_impact=ReviewImpact(
                    dimension=self.dimension.value,
                    polarity="neutral",
                    impact_level="C1",
                    confidence="medium",
                ),
            )
        ]

    def _inspect_pdf_pages_with_vlm(self, paper: dict) -> str:
        """Render and inspect PDF pages when VLM is enabled."""
        presentation_config = self.config.get("agents", {}).get("presentation", {})
        if not presentation_config.get("use_vlm", False):
            return ""
        source_path = paper.get("metadata", {}).get("source_path")
        if not source_path or Path(source_path).suffix.lower() != ".pdf":
            return ""
        max_pages = int(self.config.get("paper", {}).get("max_vlm_pages", 3))
        dpi = int(self.config.get("paper", {}).get("page_image_dpi", 160))
        output_dir = (
            Path(self.config.get("project", {}).get("output_dir", "outputs"))
            / "vlm_pages"
            / str(paper.get("id") or Path(source_path).stem)
        )
        try:
            page_images = render_pdf_pages(source_path, output_dir, max_pages=max_pages, dpi=dpi)
            if not page_images:
                return ""
            return VLMTool(self.config).inspect_pages(
                page_images,
                [
                    "Are figures and tables legible?",
                    "Are captions informative and connected to the visual content?",
                    "Are there layout, typography, equation, or formatting issues?",
                    "Is the paper easy to visually inspect as an ICLR submission?",
                ],
            )
        except Exception as exc:
            if presentation_config.get("require_vlm", False):
                raise RuntimeError("VLM inspection failed for Presentation review.") from exc
            return f"VLM inspection unavailable: {exc}"

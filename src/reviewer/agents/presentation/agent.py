"""Purpose: Presentation Agent logic."""

from __future__ import annotations

from pathlib import Path

from reviewer.agents.dimension_base import DimensionAgent
from reviewer.citation.compliance import run_compliance_checks
from reviewer.dimensions import ReviewDimension
from reviewer.schemas.qa import QAResult


class PresentationAgent(DimensionAgent):
    """Evaluate clarity, formatting, figures, tables, and readability."""

    name = "presentation"
    dimension = ReviewDimension.PRESENTATION

    def initial_qa_results(self, paper: dict, summary_xml: str) -> list[QAResult]:
        """Preload PDF guard plus deterministic compliance (hard-gate) evidence.

        Compliance checks (citation integrity, page limit) run here as preloaded
        Q&A evidence; a confirmed violation arrives tagged ``impact_level=C0`` so
        the Presentation review treats it as a must-reject hard gate.
        """
        _ = summary_xml
        presentation_config = self.config.get("agents", {}).get("presentation", {})
        require_pdf = presentation_config.get("require_pdf", True)
        if require_pdf and not _has_pdf_evidence(paper):
            raise ValueError(
                "Presentation review requires PDF evidence. Provide a PDF source path "
                "or provide paper['pdf_pages']; set agents.presentation.require_pdf=false "
                "to allow fallback."
            )
        return run_compliance_checks(self.config, paper)


def _has_pdf_evidence(paper: dict) -> bool:
    """Return whether presentation tools can access PDF text or images later."""
    if paper.get("pdf_pages"):
        return True
    source_path = paper.get("metadata", {}).get("source_path")
    return bool(source_path and Path(source_path).suffix.lower() == ".pdf")

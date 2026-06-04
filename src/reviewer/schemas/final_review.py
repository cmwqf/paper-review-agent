"""Purpose: Schema for the aggregated final review."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pydantic import BaseModel, Field

from reviewer.tools.xml_validator import validate_xml_root


class FinalReview(BaseModel):
    """Final review synthesized from all dimension reviews."""

    final_score: float = Field(ge=1.0, le=10.0)
    summary: str
    strengths: list[str] = []
    weaknesses: list[str] = []
    requested_changes: list[str] = []
    administrative_decision: str = "clear"
    administrative_reasons: list[str] = []
    confidence_score: int = Field(ge=1, le=5)
    recommendation: str | None = None


def _text(parent: ET.Element | None, child_name: str, default: str = "") -> str:
    """Read stripped child text from an XML element."""
    if parent is None:
        return default
    child = parent.find(child_name)
    if child is None or child.text is None:
        return default
    value = child.text.strip()
    return value if value else default


def _items(parent: ET.Element | None, child_name: str) -> list[str]:
    """Read list item text from a child collection."""
    if parent is None:
        return []
    group = parent.find(child_name)
    if group is None:
        return []
    return ["".join(item.itertext()).strip() for item in group.findall("item") if "".join(item.itertext()).strip()]


def parse_final_review_xml(xml_text: str) -> FinalReview:
    """Parse `<final_review>` XML into a FinalReview."""
    clean_xml = validate_xml_root(xml_text, "final_review")
    root = ET.fromstring(clean_xml)
    return FinalReview(
        final_score=float(_text(root, "final_score", "5")),
        summary=_text(root, "summary"),
        strengths=_items(root, "strengths"),
        weaknesses=_items(root, "weaknesses"),
        requested_changes=_items(root, "requested_changes"),
        administrative_decision=_text(root, "administrative_decision", "clear"),
        administrative_reasons=_items(root, "administrative_reasons"),
        confidence_score=int(_text(root, "confidence_score", "3")),
        recommendation=_text(root, "recommendation") or None,
    )

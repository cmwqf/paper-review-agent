"""Purpose: Schema for one dimension review produced after a Q&A trajectory."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pydantic import BaseModel, Field

from reviewer.tools.xml_validator import validate_xml_root


class DimensionReview(BaseModel):
    """Contribution, Soundness, or Presentation review."""

    dimension: str
    score: int = Field(ge=1, le=4)
    strengths: list[str] = []
    weaknesses: list[str] = []
    evidence_summary: str | None = None
    rationale: str


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


def parse_dimension_review_xml(xml_text: str) -> DimensionReview:
    """Parse `<dimension_review>` XML into a DimensionReview."""
    clean_xml = validate_xml_root(xml_text, "dimension_review")
    root = ET.fromstring(clean_xml)
    return DimensionReview(
        dimension=_text(root, "dimension"),
        score=int(_text(root, "score", "2")),
        strengths=_items(root, "strengths"),
        weaknesses=_items(root, "weaknesses"),
        evidence_summary=_text(root, "evidence_summary") or None,
        rationale=_text(root, "rationale"),
    )

"""Purpose: Schema for one dimension review produced after a Q&A trajectory."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pydantic import BaseModel, Field

from reviewer.tools.xml_validator import validate_xml_root


class ReviewKeyPoint(BaseModel):
    """Prioritized point carried from dimension review into final review."""

    text: str
    importance: str = "C2"
    polarity: str = "weakness"
    confidence: str = "medium"


class DimensionReview(BaseModel):
    """Contribution, Soundness, or Presentation review."""

    dimension: str
    score: int = Field(ge=1, le=4)
    key_points: list[ReviewKeyPoint] = []
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


def _key_points(parent: ET.Element | None) -> list[ReviewKeyPoint]:
    """Read prioritized key points from a dimension review."""
    if parent is None:
        return []
    group = parent.find("key_points")
    if group is None:
        return []
    points = []
    for item in group.findall("item"):
        text = "".join(item.itertext()).strip()
        if not text:
            continue
        points.append(
            ReviewKeyPoint(
                text=text,
                importance=item.attrib.get("importance", "C2"),
                polarity=item.attrib.get("polarity", "weakness"),
                confidence=item.attrib.get("confidence", "medium"),
            )
        )
    return points


def parse_dimension_review_xml(xml_text: str) -> DimensionReview:
    """Parse `<dimension_review>` XML into a DimensionReview."""
    clean_xml = validate_xml_root(xml_text, "dimension_review")
    root = ET.fromstring(clean_xml)
    return DimensionReview(
        dimension=_text(root, "dimension"),
        score=int(_text(root, "score", "2")),
        key_points=_key_points(root),
        strengths=_items(root, "strengths"),
        weaknesses=_items(root, "weaknesses"),
        evidence_summary=_text(root, "evidence_summary") or None,
        rationale=_text(root, "rationale"),
    )

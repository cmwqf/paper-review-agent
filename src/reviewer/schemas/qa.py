"""Purpose: Schema for Q&A answers and their review impact metadata."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pydantic import BaseModel, Field

from reviewer.tools.xml_validator import validate_xml_root


class ReviewImpact(BaseModel):
    """How a Q&A answer affects a dimension review."""

    dimension: str
    polarity: str
    impact_level: str
    confidence: str


class QAResult(BaseModel):
    """Structured result returned by QATool.ask."""

    question: str
    answer: str
    evidence: list[str] = Field(default_factory=list)
    retrieved_papers: list[dict] = Field(default_factory=list)
    review_impact: ReviewImpact
    trace_events: list[dict] = Field(default_factory=list)


def _text(parent: ET.Element | None, child_name: str, default: str = "") -> str:
    """Read stripped child text from an XML element."""
    if parent is None:
        return default
    child = parent.find(child_name)
    if child is None or child.text is None:
        return default
    value = child.text.strip()
    return value if value else default


def parse_qa_result_xml(xml_text: str) -> QAResult:
    """Parse `<qa_result>` XML into a QAResult."""
    clean_xml = validate_xml_root(xml_text, "qa_result")
    root = ET.fromstring(clean_xml)
    evidence = []
    evidence_el = root.find("evidence")
    if evidence_el is not None:
        for item in evidence_el.findall("item"):
            source = item.attrib.get("source")
            text = "".join(item.itertext()).strip()
            if text:
                evidence.append(f"{source}: {text}" if source else text)

    retrieved_papers = []
    retrieved_el = root.find("retrieved_papers")
    if retrieved_el is not None:
        for paper_el in retrieved_el.findall("paper"):
            retrieved_papers.append(
                {
                    "title": _text(paper_el, "title"),
                    "year": _text(paper_el, "year"),
                    "url": _text(paper_el, "url"),
                    "relevance": _text(paper_el, "relevance"),
                }
            )

    impact_el = root.find("review_impact")
    return QAResult(
        question=_text(root, "question"),
        answer=_text(root, "answer"),
        evidence=evidence,
        retrieved_papers=retrieved_papers,
        review_impact=ReviewImpact(
            dimension=_text(impact_el, "dimension"),
            polarity=_text(impact_el, "polarity", "weakness"),
            impact_level=_text(impact_el, "impact_level", "C1"),
            confidence=_text(impact_el, "confidence", "low"),
        ),
    )

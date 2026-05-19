"""Purpose: Generic paper map schema and XML parsing for Summary Agent output."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pydantic import BaseModel

from reviewer.tools.xml_validator import validate_xml_root


class SummaryMetadata(BaseModel):
    """Metadata extracted from the paper summary XML."""

    title: str | None = None
    authors: str | None = None
    venue: str | None = None
    submission_date: str | None = None


class KeyItem(BaseModel):
    """One compact fact attached to a paper section."""

    type: str
    text: str
    location_hint: str | None = None


class PaperSection(BaseModel):
    """One section entry in the paper map."""

    section_id: str
    title: str
    summary: str
    key_items: list[KeyItem] = []


class IndexedItem(BaseModel):
    """One globally indexed item, optionally linked to a section."""

    text: str
    section_ref: str | None = None


class GlobalIndex(BaseModel):
    """Compact index of important paper entities and claims."""

    claims: list[IndexedItem] = []
    method_components: list[IndexedItem] = []
    datasets: list[IndexedItem] = []
    baselines: list[IndexedItem] = []
    ablations: list[IndexedItem] = []
    metrics: list[IndexedItem] = []
    results: list[IndexedItem] = []
    stated_limitations: list[IndexedItem] = []


class SummarySchema(BaseModel):
    """Internal JSON-friendly representation of `<paper_summary>` XML."""

    metadata: SummaryMetadata
    paper_map: list[PaperSection] = []
    global_index: GlobalIndex = GlobalIndex()
    raw_xml: str | None = None


def _text(parent: ET.Element | None, child_name: str, default: str = "unknown") -> str:
    """Read stripped child text from an XML element."""
    if parent is None:
        return default
    child = parent.find(child_name)
    if child is None or child.text is None:
        return default
    value = child.text.strip()
    return value if value else default


def _indexed_items(parent: ET.Element | None, group_name: str) -> list[IndexedItem]:
    """Parse a global-index group into indexed items."""
    if parent is None:
        return []
    group = parent.find(group_name)
    if group is None:
        return []
    items = []
    for item in group.findall("item"):
        text = "".join(item.itertext()).strip()
        if text:
            items.append(IndexedItem(text=text, section_ref=item.attrib.get("section_ref")))
    return items


def parse_summary_xml(xml_text: str) -> SummarySchema:
    """Parse Summary Agent XML into an internal JSON-friendly schema."""
    clean_xml = validate_xml_root(xml_text, "paper_summary")
    root = ET.fromstring(clean_xml)

    metadata_el = root.find("metadata")
    metadata = SummaryMetadata(
        title=_text(metadata_el, "title"),
        authors=_text(metadata_el, "authors"),
        venue=_text(metadata_el, "venue"),
        submission_date=_text(metadata_el, "submission_date"),
    )

    sections: list[PaperSection] = []
    paper_map_el = root.find("paper_map")
    if paper_map_el is not None:
        for idx, section_el in enumerate(paper_map_el.findall("section"), start=1):
            key_items = []
            key_items_el = section_el.find("key_items")
            if key_items_el is not None:
                for item_el in key_items_el.findall("item"):
                    item_type = _text(item_el, "type", default="other")
                    item_text = _text(item_el, "text", default="")
                    location_hint = _text(item_el, "location_hint", default="")
                    if item_text:
                        key_items.append(
                            KeyItem(
                                type=item_type,
                                text=item_text,
                                location_hint=location_hint or None,
                            )
                        )
            sections.append(
                PaperSection(
                    section_id=_text(section_el, "section_id", default=f"s{idx}"),
                    title=_text(section_el, "title", default=f"Section {idx}"),
                    summary=_text(section_el, "summary", default=""),
                    key_items=key_items,
                )
            )

    global_index_el = root.find("global_index")
    global_index = GlobalIndex(
        claims=_indexed_items(global_index_el, "claims"),
        method_components=_indexed_items(global_index_el, "method_components"),
        datasets=_indexed_items(global_index_el, "datasets"),
        baselines=_indexed_items(global_index_el, "baselines"),
        ablations=_indexed_items(global_index_el, "ablations"),
        metrics=_indexed_items(global_index_el, "metrics"),
        results=_indexed_items(global_index_el, "results"),
        stated_limitations=_indexed_items(global_index_el, "stated_limitations"),
    )

    return SummarySchema(
        metadata=metadata,
        paper_map=sections,
        global_index=global_index,
        raw_xml=clean_xml,
    )


def _render_index_group(name: str, items: list[IndexedItem], max_items: int) -> list[str]:
    """Render one global-index group into compact text lines."""
    if not items:
        return []
    lines = [f"{name}:"]
    for item in items[:max_items]:
        ref = f"[{item.section_ref}] " if item.section_ref else ""
        lines.append(f"- {ref}{item.text}")
    if len(items) > max_items:
        lines.append(f"- ... {len(items) - max_items} more")
    return lines


def render_summary_for_agent(
    summary: SummarySchema,
    *,
    max_sections: int = 8,
    max_key_items_per_section: int = 6,
    max_index_items_per_group: int = 8,
) -> str:
    """Render a paper-map summary into compact text for downstream agents.

    JSON is useful for storage and programmatic access, but this text form is
    easier for LLM agents to read. It preserves section IDs and location hints
    so AnswerAgent can decide what to search or read in the original paper.
    """
    lines: list[str] = ["PAPER MAP"]
    metadata = summary.metadata
    lines.append(f"Title: {metadata.title or 'unknown'}")
    if metadata.authors:
        lines.append(f"Authors: {metadata.authors}")
    if metadata.venue:
        lines.append(f"Venue: {metadata.venue}")
    if metadata.submission_date:
        lines.append(f"Submission date: {metadata.submission_date}")

    lines.append("")
    lines.append("SECTIONS")
    for section in summary.paper_map[:max_sections]:
        lines.append(f"[{section.section_id}] {section.title}")
        if section.summary:
            lines.append(f"Summary: {section.summary}")
        if section.key_items:
            lines.append("Key items:")
            for item in section.key_items[:max_key_items_per_section]:
                location = f" ({item.location_hint})" if item.location_hint else ""
                lines.append(f"- {item.type}{location}: {item.text}")
            if len(section.key_items) > max_key_items_per_section:
                lines.append(f"- ... {len(section.key_items) - max_key_items_per_section} more")
        lines.append("")

    if len(summary.paper_map) > max_sections:
        lines.append(f"... {len(summary.paper_map) - max_sections} more sections")
        lines.append("")

    lines.append("GLOBAL INDEX")
    index = summary.global_index
    groups = [
        ("Claims", index.claims),
        ("Method components", index.method_components),
        ("Datasets", index.datasets),
        ("Baselines", index.baselines),
        ("Ablations", index.ablations),
        ("Metrics", index.metrics),
        ("Results", index.results),
        ("Stated limitations", index.stated_limitations),
    ]
    for group_name, items in groups:
        rendered = _render_index_group(group_name, items, max_index_items_per_group)
        if rendered:
            lines.extend(rendered)

    return "\n".join(lines).strip() + "\n"

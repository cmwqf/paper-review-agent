"""Purpose: Validate and repair XML outputs produced by model calls."""

from __future__ import annotations

import xml.etree.ElementTree as ET


def parse_xml(xml_text: str) -> ET.Element:
    """Parse XML text and raise a standard ParseError on invalid XML."""
    return ET.fromstring(xml_text)


def extract_xml_document(text: str, root_tag: str) -> str:
    """Extract one XML document from model text by root tag.

    Models sometimes wrap XML in markdown or add short prefaces. This helper
    keeps the workflow tolerant while still validating the extracted XML.
    """
    start_token = f"<{root_tag}"
    end_token = f"</{root_tag}>"
    start = text.find(start_token)
    end = text.rfind(end_token)
    if start == -1 or end == -1:
        return text.strip()
    return text[start : end + len(end_token)].strip()


def validate_xml_root(xml_text: str, root_tag: str) -> str:
    """Validate XML and require the expected root tag.

    Returns the extracted XML string so callers can save a clean document.
    """
    extracted = extract_xml_document(xml_text, root_tag)
    if not extracted.strip():
        raise ValueError(f"Expected <{root_tag}> XML, but model output was empty.")
    root = parse_xml(extracted)
    if root.tag != root_tag:
        raise ValueError(f"Expected XML root <{root_tag}>, got <{root.tag}>.")
    return extracted

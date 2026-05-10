"""Purpose: XML serialization and parsing helpers for schema-backed outputs."""

from __future__ import annotations

import xml.etree.ElementTree as ET


def root_tag(xml_text: str) -> str:
    """Return the root tag for a model-produced XML document."""
    return ET.fromstring(xml_text).tag


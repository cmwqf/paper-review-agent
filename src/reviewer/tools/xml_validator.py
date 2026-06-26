"""Purpose: Validate and repair XML outputs produced by model calls."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable

# A bare ``&`` is only legal as the start of a character/entity reference such
# as ``&amp;``, ``&#10;`` or ``&#x1F;``. Anything else (``Smith & Jones``,
# ``a&b`` in a URL, ``&`` in a BibTeX entry) is an "invalid token" to ET.
_BARE_AMP = re.compile(r"&(?!(?:#[0-9]+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9._-]*);)")

# An XML name (tag) per the relevant subset of the spec: a letter-led token.
_NAME = r"[A-Za-z][A-Za-z0-9_.:-]*"

# A ``<``/``</`` that begins a tag-like token, capturing ``/`` (close) and name.
_LT_TOKEN = re.compile(rf"<(/?)({_NAME})?")

# Closing tags ``</name>`` and self-closing tags ``<name .../>`` reveal the
# names the document actually uses as markup; everything else that looks like a
# tag (``<eos>``, ``<mask>``) is almost certainly literal text.
_CLOSE_TAG = re.compile(rf"</({_NAME})\s*>")
_SELFCLOSE_TAG = re.compile(rf"<({_NAME})(?:\s[^<>]*?)?/>")


def _structural_tag_names(text: str) -> set[str]:
    """Derive the whitelist of real tag names from the document itself.

    A name counts as structural markup if it appears as a closing tag
    (``</name>``) or a self-closing tag (``<name/>``). Special tokens like
    ``<eos>`` never close, so they are excluded and get escaped as text.
    """
    return set(_CLOSE_TAG.findall(text)) | set(_SELFCLOSE_TAG.findall(text))


def sanitize_xml(xml_text: str, known_tags: Iterable[str] | None = None) -> str:
    """Escape stray ``&`` and ``<`` that models leave unescaped in text content.

    Academic content routinely contains literal ``&`` (citations, BibTeX, URLs)
    and ``<`` (math inequalities, special tokens like ``<sos>``, ``<eos>``)
    inside element text, which makes ``ET.fromstring`` raise ``ParseError: not
    well-formed (invalid token)``. This deterministically escapes those stray
    characters while preserving genuine tags and existing entity references, so
    a paper is not lost to a single unescaped symbol.

    A ``<`` followed by a letter is ambiguous (``<eos>`` vs. a real ``<tag>``).
    It is resolved against a whitelist of tag names: ``known_tags`` when the
    caller supplies one, otherwise the set of names the document uses as
    closing/self-closing tags. Names outside the whitelist are treated as
    literal text and escaped.
    """
    text = _BARE_AMP.sub("&amp;", xml_text)
    allowed = set(known_tags) if known_tags is not None else _structural_tag_names(text)

    def _replace(match: re.Match[str]) -> str:
        nxt = text[match.end() : match.end() + 1]
        # Comments, CDATA, doctype and processing instructions: never escape.
        if match.group(0) == "<" and nxt in ("!", "?"):
            return "<"
        name = match.group(2)
        # ``<`` before a space/digit/punctuation, or a tag name not in the
        # whitelist, is literal text.
        if name is None or name not in allowed:
            return "&lt;" + (match.group(1) or "") + (name or "")
        return match.group(0)

    return _LT_TOKEN.sub(_replace, text)


def parse_xml(xml_text: str) -> ET.Element:
    """Parse XML text, escaping stray special characters on a first failure.

    Valid documents are parsed untouched; only when strict parsing fails do we
    retry against a sanitized copy. If both fail the original ParseError (with
    its line/column) propagates so callers see the real location.
    """
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError:
        sanitized = sanitize_xml(xml_text)
        if sanitized == xml_text:
            raise
        return ET.fromstring(sanitized)


def extract_xml_document(text: str, root_tag: str) -> str:
    """Extract one XML document from model text by root tag.

    Models sometimes wrap XML in markdown or add short prefaces. This helper
    keeps the workflow tolerant while still validating the extracted XML.
    """
    start_token = f"<{root_tag}"
    end_token = f"</{root_tag}>"
    start = text.find(start_token)
    end = text.find(end_token, start + len(start_token))
    if start == -1 or end == -1:
        return text.strip()
    return text[start : end + len(end_token)].strip()


def validate_xml_root(xml_text: str, root_tag: str) -> str:
    """Validate XML and require the expected root tag.

    Returns the extracted (and, when needed, sanitized) XML string so callers
    can both save and re-parse a clean document.
    """
    extracted = extract_xml_document(xml_text, root_tag)
    if not extracted.strip():
        raise ValueError(f"Expected <{root_tag}> XML, but model output was empty.")
    try:
        root = ET.fromstring(extracted)
    except ET.ParseError:
        sanitized = sanitize_xml(extracted)
        if sanitized == extracted:
            raise
        root = ET.fromstring(sanitized)
        extracted = sanitized
    if root.tag != root_tag:
        raise ValueError(f"Expected XML root <{root_tag}>, got <{root.tag}>.")
    return extracted

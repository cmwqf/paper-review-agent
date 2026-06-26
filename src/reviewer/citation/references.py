"""Purpose: Extract a structured reference list from raw paper text via the LLM.

Bibliography entries in the benchmark markdown are noisy (OCR artifacts, titles
sometimes italicized and sometimes not, authors/venue interleaved), so a regex
parser is brittle. We slice out the references section deterministically, then
let the LLM normalize each entry into {index, title, arxiv_id, doi, year}.
"""

from __future__ import annotations

import json
import logging
import re

from reviewer.models.factory import build_llm

LOGGER = logging.getLogger(__name__)

# Match a references/bibliography heading in BOTH markdown ("# REFERENCES") and
# raw PDF-extracted text ("REFERENCES" on its own line, optionally numbered).
# Requiring the heading word to stand alone on the line avoids matching inline
# mentions like "see the references section".
_REF_HEADING = re.compile(
    r"^[ \t>#*]*(?:\d+\.?\s*|[A-Z]\.?\s+)?(references|bibliography)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_NEXT_H1 = re.compile(r"^\s{0,3}#\s+\S", re.MULTILINE)

_EXTRACT_SYSTEM = (
    "You normalize an academic paper's reference list into structured data. "
    "For every distinct bibliography entry, output its citation index, the work's "
    "TITLE ONLY (exclude authors, venue, pages, and year), and any arXiv id or DOI "
    "that appears in the entry. Do not invent, correct, complete, or merge entries; "
    "copy titles verbatim even if they look wrong. Ignore stray numbers and OCR noise.\n\n"
    "Output ONLY a JSON array, no prose, no code fences. Each element:\n"
    '{"index": "12", "title": "...", "arxiv_id": "2204.05862" or null, '
    '"doi": "..." or null, "year": 2022 or null}'
)


def slice_references_section(text: str) -> str:
    """Return the references/bibliography section text, or '' if none found."""
    match = _REF_HEADING.search(text or "")
    if not match:
        return ""
    rest = text[match.end():]
    nxt = _NEXT_H1.search(rest)
    section = rest[: nxt.start()] if nxt else rest
    return section.strip()


def extract_references(config: dict, text: str, *, max_refs: int = 100) -> list[dict]:
    """Extract structured references from paper text; [] when none are found."""
    section = slice_references_section(text)
    if not section:
        LOGGER.info("Citation integrity: no references/bibliography section found.")
        return []
    settings = config.get("compliance", {})
    client = build_llm(config, settings.get("extract_model", "summary"))
    max_chars = int(settings.get("max_section_chars", 40000))
    raw = client.generate(
        [
            {"role": "system", "content": _EXTRACT_SYSTEM},
            {"role": "user", "content": f"Reference list:\n\n{section[:max_chars]}"},
        ]
    )
    refs = _parse_reference_json(raw)
    return refs[:max_refs]


def _parse_reference_json(raw: str) -> list[dict]:
    """Parse the LLM's JSON array of references, tolerating code fences."""
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        LOGGER.warning("Citation integrity: reference extraction returned no JSON array.")
        return []
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        LOGGER.warning("Citation integrity: reference JSON failed to parse.")
        return []
    refs: list[dict] = []
    for item in data if isinstance(data, list) else []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        refs.append(
            {
                "index": str(item.get("index") or "").strip(),
                "title": title,
                "arxiv_id": _clean_id(item.get("arxiv_id")),
                "doi": _clean_id(item.get("doi")),
                "year": item.get("year"),
            }
        )
    return refs


def _clean_id(value: object) -> str | None:
    """Normalize an arXiv/DOI id, returning None for empty/placeholder values."""
    if not value:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "n/a"}:
        return None
    return text.replace("arXiv:", "").replace("arxiv:", "").strip()

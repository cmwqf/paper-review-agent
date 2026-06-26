"""Purpose: Verify whether a single cited reference actually exists.

Precision-first: a reference is only labelled ``nonexistent`` when the title
match endpoint returns no match AND a fallback keyword search also surfaces no
close title. Anything ambiguous — short/generic titles, rate-limit failures, a
low-similarity match — is ``unverifiable`` (NOT a violation), because "couldn't
find it" must never be mistaken for "it was fabricated".
"""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher

from reviewer.retrieval.semantic_scholar import SemanticScholarClient
from reviewer.schemas.integrity import CitationFinding

LOGGER = logging.getLogger(__name__)

_MIN_TITLE_CHARS = 25
_MIN_TITLE_WORDS = 4
_SIMILAR_THRESHOLD = 0.62


def _normalize(title: str) -> str:
    """Lowercase and strip punctuation/whitespace for title comparison."""
    return re.sub(r"[^a-z0-9 ]+", "", title.lower()).strip()


def title_similarity(a: str, b: str) -> float:
    """Return a 0..1 similarity between two titles."""
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def verify_reference(client: SemanticScholarClient, ref: dict) -> CitationFinding:
    """Classify one reference as exists / nonexistent / unverifiable."""
    title = str(ref.get("title") or "").strip()
    arxiv_id = ref.get("arxiv_id")
    doi = ref.get("doi")
    finding = CitationFinding(
        index=str(ref.get("index") or ""), title=title, arxiv_id=arxiv_id, doi=doi
    )

    # 1) A resolvable external id is decisive proof the work exists.
    for id_type, id_value in (("ARXIV", arxiv_id), ("DOI", doi)):
        if not id_value:
            continue
        try:
            hit = client.lookup_external_id(id_type, id_value)
        except Exception as exc:  # rate-limit / network — fall through to title
            LOGGER.info("Citation integrity: %s lookup failed for %r: %s", id_type, id_value, exc)
            hit = None
        if hit:
            finding.status = "exists"
            finding.confidence = "high"
            finding.matched_title = str(hit.get("title") or "")
            finding.evidence = f"Resolved by {id_type} id {id_value}."
            return finding

    # 2) Titles too short/generic cannot be safely judged absent.
    if len(title) < _MIN_TITLE_CHARS or len(title.split()) < _MIN_TITLE_WORDS:
        finding.status = "unverifiable"
        finding.confidence = "low"
        finding.evidence = "Title too short/generic to verify existence reliably."
        return finding

    # 3) Best-title-match endpoint (404 => no close match in the corpus).
    try:
        match = client.match(title)
    except Exception as exc:  # persistent rate-limit / network
        finding.status = "unverifiable"
        finding.confidence = "low"
        finding.evidence = f"Title lookup did not complete ({exc})."
        return finding

    if match is not None:
        matched_title = str(match.get("title") or "")
        score = title_similarity(title, matched_title)
        finding.matched_title = matched_title
        finding.match_score = round(score, 3)
        if score >= _SIMILAR_THRESHOLD:
            finding.status = "exists"
            finding.confidence = "high"
            finding.evidence = f"Matched existing paper (similarity {score:.2f})."
        else:
            finding.status = "unverifiable"
            finding.confidence = "low"
            finding.evidence = (
                f"Match endpoint returned a low-similarity title ({score:.2f}); inconclusive."
            )
        return finding

    # 4) No title match — confirm with a fallback keyword search before accusing.
    try:
        results = client.search(title, limit=5)
    except Exception as exc:
        finding.status = "unverifiable"
        finding.confidence = "low"
        finding.evidence = f"No title match; fallback search failed ({exc})."
        return finding

    best = max((title_similarity(title, r.title) for r in results), default=0.0)
    if best >= _SIMILAR_THRESHOLD:
        finding.status = "unverifiable"
        finding.confidence = "low"
        finding.match_score = round(best, 3)
        finding.evidence = (
            f"No exact match (404) but a close title appeared in search ({best:.2f}); inconclusive."
        )
        return finding

    finding.status = "nonexistent"
    finding.confidence = "high"
    finding.match_score = round(best, 3)
    finding.evidence = (
        "No title match from the match endpoint (404) and no close title in a "
        f"fallback keyword search (best similarity {best:.2f})."
    )
    return finding

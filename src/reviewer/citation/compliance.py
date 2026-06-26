"""Purpose: Deterministic compliance checks fed into the Presentation review.

Hard, reject-worthy violations (fabricated references, page-limit overruns) are
not a separate review dimension — in real venues they are administrative checks
that a human reviewer/AC folds into the Presentation/format assessment. So we
run them deterministically here and hand the Presentation agent preloaded Q&A
evidence: a *confirmed* violation is tagged ``impact_level=C0`` (the existing
hard-gate that drives a Reject), while merely *suspected* issues are tagged a
softer level so they are flagged, not auto-rejected.

The precision threshold lives in this deterministic code; the Presentation
prompt only has to state that a confirmed C0 compliance finding means reject.
"""

from __future__ import annotations

import logging
import re
import time

from reviewer.citation.references import _REF_HEADING, extract_references
from reviewer.citation.verify import verify_reference
from reviewer.retrieval.semantic_scholar import SemanticScholarClient
from reviewer.schemas.qa import QAResult, ReviewImpact

LOGGER = logging.getLogger(__name__)

_PAGE_MARKER = re.compile(r"=== Page (\d+) ===")


def run_compliance_checks(config: dict, paper: dict) -> list[QAResult]:
    """Run enabled compliance checks and return them as Presentation Q&A evidence."""
    settings = config.get("compliance", {})
    if not settings.get("enabled", True):
        return []
    results: list[QAResult] = []
    if settings.get("check_citations", True):
        results.extend(_citation_evidence(config, paper, settings))
    if settings.get("check_page_limit", True):
        page = _page_limit_evidence(config, paper, settings)
        if page is not None:
            results.append(page)
    return results


def _qa(
    *, qa_id: str, question: str, answer: str, evidence: list[str], polarity: str, impact_level: str
) -> QAResult:
    """Build one preloaded Presentation Q&A evidence item."""
    return QAResult(
        id=qa_id,
        question=question,
        answer=answer,
        evidence=evidence,
        review_impact=ReviewImpact(
            dimension="Presentation", polarity=polarity, impact_level=impact_level, confidence="high"
        ),
    )


def _citation_evidence(config: dict, paper: dict, settings: dict) -> list[QAResult]:
    """Verify cited references exist; flag confirmed fabrication as a C0 hard gate."""
    refs = extract_references(config, str(paper.get("text") or ""))
    if not refs:
        return []
    max_checked = int(settings.get("max_refs_checked", 60))
    delay = float(settings.get("request_delay_seconds", 1.0))
    threshold = int(settings.get("hard_gate_min_nonexistent", 3))

    client = SemanticScholarClient(config)
    checked = refs[:max_checked]
    findings = []
    for ref in checked:
        findings.append(verify_reference(client, ref))
        if delay > 0:
            time.sleep(delay)

    nonexistent = [f for f in findings if f.status == "nonexistent"]
    n = len(nonexistent)
    detail = [f"[{f.index or '?'}] {f.title!r}: {f.evidence}" for f in nonexistent]
    if len(refs) > len(checked):
        detail.append(f"(Only the first {len(checked)} of {len(refs)} references were checked.)")

    if n >= threshold:
        polarity, impact = "weakness", "C0"
        answer = (
            f"MUST-REJECT (citation integrity): {n} cited references could not be verified to "
            "exist and appear fabricated, indicating a non-genuine bibliography."
        )
    elif n >= 1:
        polarity, impact = "weakness", "C2"
        answer = (
            f"{n} cited reference(s) could not be verified to exist. Treat as a suspected issue "
            "for the authors to clarify, not a confirmed fabrication on its own."
        )
    else:
        polarity, impact = "strength", "C4"
        answer = f"All {len(findings)} checked references resolved to existing papers."
        detail = ["No unverifiable references among those checked."]

    LOGGER.info("Compliance(citations): checked=%s nonexistent=%s impact=%s", len(findings), n, impact)
    return [
        _qa(
            qa_id="PRES-COMPLIANCE-CITATIONS",
            question="Do all cited references correspond to real, existing papers?",
            answer=answer,
            evidence=detail,
            polarity=polarity,
            impact_level=impact,
        )
    ]


def _page_limit_evidence(config: dict, paper: dict, settings: dict) -> QAResult | None:
    """Flag a main-text page-limit overrun as a C0 hard gate (PDF inputs only)."""
    venue = str(
        paper.get("metadata", {}).get("venue")
        or config.get("review", {}).get("rubric_profile")
        or ""
    ).upper()
    limit = settings.get("page_limits", {}).get(venue)
    if not limit:
        return None
    main_pages = _main_text_pages(str(paper.get("text") or ""))
    if main_pages is None:
        return None  # no page information (e.g. markdown input) — cannot judge

    buffer = int(settings.get("page_limit_buffer", 0))
    if main_pages > int(limit) + buffer:
        return _qa(
            qa_id="PRES-COMPLIANCE-PAGES",
            question="Does the paper comply with the venue main-text page limit?",
            answer=(
                f"MUST-REJECT (page limit): main text spans {main_pages} pages, exceeding the "
                f"{venue} limit of {limit}."
            ),
            evidence=[f"References section begins after page {main_pages}; {venue} limit is {limit}."],
            polarity="weakness",
            impact_level="C0",
        )
    return _qa(
        qa_id="PRES-COMPLIANCE-PAGES",
        question="Does the paper comply with the venue main-text page limit?",
        answer=f"Main text is {main_pages} pages, within the {venue} limit of {limit}.",
        evidence=[f"Main text ends by page {main_pages}; {venue} limit is {limit}."],
        polarity="strength",
        impact_level="C4",
    )


def _main_text_pages(text: str) -> int | None:
    """Return the page number where the references section begins, or None.

    Uses ``=== Page N ===`` markers (present for PDF inputs). Main-text length is
    approximated by the highest page number appearing before the references heading.
    """
    if "=== Page" not in text:
        return None
    ref_match = _REF_HEADING.search(text)
    if ref_match is None:
        # Without a references boundary we cannot tell main text from appendices,
        # so do not guess (guessing here previously counted the whole PDF and
        # produced a false page-limit violation).
        return None
    head = text[: ref_match.start()]
    pages = [int(n) for n in _PAGE_MARKER.findall(head)]
    return max(pages) if pages else None

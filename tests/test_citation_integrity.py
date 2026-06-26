"""Purpose: Tests for citation/page compliance checks without network or LLM."""

from __future__ import annotations

from reviewer.citation.compliance import _main_text_pages, run_compliance_checks
from reviewer.citation.references import _parse_reference_json, slice_references_section
from reviewer.citation.verify import title_similarity, verify_reference


class FakeS2:
    """Fake Semantic Scholar client driven by canned per-title behavior."""

    def __init__(self, *, matches=None, ext_ids=None, search_hits=None):
        self.matches = matches or {}
        self.ext_ids = ext_ids or {}
        self.search_hits = search_hits or {}

    def match(self, title):
        return self.matches.get(title)

    def lookup_external_id(self, id_type, id_value):
        return self.ext_ids.get((id_type, id_value))

    def search(self, query, limit=5):
        return self.search_hits.get(query, [])


class _Hit:
    def __init__(self, title):
        self.title = title


def test_slice_references_section() -> None:
    text = "# Intro\nbody\n# References\n- [1] A real paper title here.\n# Appendix\nstuff"
    section = slice_references_section(text)
    assert "[1] A real paper title here." in section
    assert "Appendix" not in section and "Intro" not in section


def test_parse_reference_json_tolerates_fences() -> None:
    raw = '```json\n[{"index":"1","title":"Deep learning of things","arxiv_id":"2101.00001"}]\n```'
    refs = _parse_reference_json(raw)
    assert refs == [
        {"index": "1", "title": "Deep learning of things", "arxiv_id": "2101.00001", "doi": None, "year": None}
    ]


def test_verify_exists_via_arxiv_id() -> None:
    client = FakeS2(ext_ids={("ARXIV", "2204.05862"): {"title": "Training a helpful assistant"}})
    finding = verify_reference(client, {"index": "4", "title": "Training a helpful assistant", "arxiv_id": "2204.05862"})
    assert finding.status == "exists" and finding.confidence == "high"


def test_verify_exists_via_title_match() -> None:
    title = "Language models are few-shot learners"
    client = FakeS2(matches={title: {"title": title}})
    assert verify_reference(client, {"index": "5", "title": title}).status == "exists"


def test_verify_nonexistent_requires_404_and_empty_fallback() -> None:
    title = "Quantum entangled transformers for telepathic reasoning"
    client = FakeS2(matches={title: None}, search_hits={title: []})
    finding = verify_reference(client, {"index": "9", "title": title})
    assert finding.status == "nonexistent" and finding.confidence == "high"


def test_verify_unverifiable_when_fallback_finds_close_title() -> None:
    title = "Towards reliable LLM evaluations: lessons from assessment"
    client = FakeS2(matches={title: None}, search_hits={title: [_Hit(title)]})
    assert verify_reference(client, {"index": "9", "title": title}).status == "unverifiable"


def test_verify_unverifiable_for_short_generic_title() -> None:
    finding = verify_reference(FakeS2(), {"index": "1", "title": "A short title"})
    assert finding.status == "unverifiable" and finding.confidence == "low"


def test_title_similarity_basic() -> None:
    assert title_similarity("Attention Is All You Need", "Attention is all you need") > 0.95
    assert title_similarity("Deep residual learning", "A totally different paper") < 0.5


# --- Compliance evidence (folded into Presentation) -------------------------

_CFG = {"compliance": {"request_delay_seconds": 0, "hard_gate_min_nonexistent": 3}}


def _patch_refs(monkeypatch, refs):
    monkeypatch.setattr("reviewer.citation.compliance.extract_references", lambda cfg, text, **k: refs)


def test_compliance_single_fabrication_is_soft_flag(monkeypatch) -> None:
    """One nonexistent reference -> soft flag (not C0), never an auto-reject."""
    _patch_refs(monkeypatch, [
        {"index": "1", "title": "Language models are few-shot learners"},
        {"index": "2", "title": "Quantum entangled transformers for telepathic reasoning"},
    ])
    fake = FakeS2(
        matches={
            "Language models are few-shot learners": {"title": "Language models are few-shot learners"},
            "Quantum entangled transformers for telepathic reasoning": None,
        },
        search_hits={"Quantum entangled transformers for telepathic reasoning": []},
    )
    monkeypatch.setattr("reviewer.citation.compliance.SemanticScholarClient", lambda cfg: fake)
    results = run_compliance_checks({"compliance": {"request_delay_seconds": 0, "check_page_limit": False}}, {"text": "x"})
    cite = next(r for r in results if r.id == "PRES-COMPLIANCE-CITATIONS")
    assert cite.review_impact.impact_level == "C2"      # soft flag, not C0
    assert cite.review_impact.polarity == "weakness"


def test_compliance_systematic_fabrication_is_c0(monkeypatch) -> None:
    """>= threshold nonexistent references -> C0 must-reject hard gate."""
    fakes = [f"Fabricated nonexistent paper number {i} about nothing real" for i in range(3)]
    _patch_refs(monkeypatch, [{"index": str(i), "title": t} for i, t in enumerate(fakes)])
    fake = FakeS2(matches={t: None for t in fakes}, search_hits={t: [] for t in fakes})
    monkeypatch.setattr("reviewer.citation.compliance.SemanticScholarClient", lambda cfg: fake)
    results = run_compliance_checks(_CFG, {"text": "x"})
    cite = next(r for r in results if r.id == "PRES-COMPLIANCE-CITATIONS")
    assert cite.review_impact.impact_level == "C0"
    assert cite.answer.startswith("MUST-REJECT")


def test_main_text_pages_from_markers() -> None:
    text = "=== Page 1 ===\na\n=== Page 2 ===\nb\n# References\n=== Page 3 ===\nrefs"
    assert _main_text_pages(text) == 2  # refs heading is after page 2
    assert _main_text_pages("no markers here") is None


def test_main_text_pages_none_without_refs_boundary() -> None:
    """No references heading -> skip (do not count the whole doc -> no false flag)."""
    text = "=== Page 1 ===\na\n=== Page 2 ===\nb\n=== Page 3 ===\nappendix"
    assert _main_text_pages(text) is None


def test_slice_references_section_plain_text_heading() -> None:
    """PDF-extracted text has no markdown '#'; a bare REFERENCES line must match."""
    text = "=== Page 10 ===\nbody\nREFERENCES\n[1] A real paper title here. 2023."
    section = slice_references_section(text)
    assert "[1] A real paper title here." in section


def test_slice_references_ignores_inline_mention() -> None:
    """An inline mention of 'references' must not be treated as the heading."""
    text = "We compare to prior references in Table 2 and discuss them below."
    assert slice_references_section(text) == ""


def test_page_limit_violation_is_c0(monkeypatch) -> None:
    """Main text over the venue limit -> C0 must-reject."""
    _patch_refs(monkeypatch, [])  # skip citation API
    text = "".join(f"=== Page {i} ===\ntext\n" for i in range(1, 13)) + "# References\n=== Page 13 ===\n"
    paper = {"text": text, "pdf_pages": ["x"] * 13, "metadata": {"venue": "ICLR"}}
    config = {
        "compliance": {"check_citations": False, "page_limits": {"ICLR": 10}},
        "review": {"rubric_profile": "ICLR"},
    }
    results = run_compliance_checks(config, paper)
    pages = next(r for r in results if r.id == "PRES-COMPLIANCE-PAGES")
    assert pages.review_impact.impact_level == "C0"
    assert "MUST-REJECT" in pages.answer


def test_page_limit_skipped_without_markers(monkeypatch) -> None:
    """Markdown input (no page markers) cannot be judged -> no page finding."""
    _patch_refs(monkeypatch, [])
    config = {"compliance": {"check_citations": False, "page_limits": {"ICLR": 10}}, "review": {"rubric_profile": "ICLR"}}
    results = run_compliance_checks(config, {"text": "plain markdown, no page markers", "metadata": {"venue": "ICLR"}})
    assert not any(r.id == "PRES-COMPLIANCE-PAGES" for r in results)

"""Purpose: Tests for DeepReview-Bench paper loading."""

from __future__ import annotations

import json

from reviewer.paper.bench_loader import load_bench_paper, load_bench_split


def test_load_bench_split_reads_rows(tmp_path) -> None:
    split = tmp_path / "split.jsonl"
    split.write_text('{"id":"a"}\n{"id":"b"}\n', encoding="utf-8")

    assert load_bench_split(split) == [{"id": "a"}, {"id": "b"}]


def test_load_bench_paper_resolves_markdown_pdf_and_metadata(tmp_path) -> None:
    bench_root = tmp_path / "bench"
    paper_dir = bench_root / "papers" / "abc"
    paper_dir.mkdir(parents=True)
    (paper_dir / "paper.pdf").write_bytes(b"fake")
    (paper_dir / "paper.md").write_text("# Bench Paper\n\nBody text.", encoding="utf-8")
    figures_dir = paper_dir / "figures"
    figures_dir.mkdir()
    (figures_dir / "_page_4_Figure_2.jpeg").write_bytes(b"figure")
    (paper_dir / "metadata.json").write_text(
        json.dumps(
            {
                "id": "abc",
                "title": "Bench Paper",
                "venue": "ICLR",
                "venue_year": 2024,
                "decision": "Reject",
                "date": "2023-10-18",
                "openreview_pdf_url": "https://example.com/pdf",
            }
        ),
        encoding="utf-8",
    )
    (paper_dir / "review.json").write_text('{"reviews":[]}', encoding="utf-8")

    paper = load_bench_paper(
        {"id": "abc", "source_file": "source.jsonl", "source_index": 7},
        bench_root,
    )

    assert paper["id"] == "abc"
    assert paper["title"] == "Bench Paper"
    assert paper["text"] == "# Bench Paper\n\nBody text."
    assert paper["metadata"]["source"] == "DeepReview-Bench"
    assert paper["metadata"]["source_path"].endswith("paper.pdf")
    assert paper["metadata"]["markdown_path"].endswith("paper.md")
    assert paper["metadata"]["figures_dir"].endswith("figures")
    assert paper["metadata"]["submission_date"] == "2023-10-18"
    assert paper["metadata"]["split_source_index"] == 7
    assert paper["figures"] == [
        {
            "label": "Figure 2",
            "kind": "Figure",
            "number": "2",
            "path": str(figures_dir / "_page_4_Figure_2.jpeg"),
            "filename": "_page_4_Figure_2.jpeg",
            "page_index": 4,
            "pdf_page": 5,
        }
    ]
    assert paper["raw"]["metadata"]["venue"] == "ICLR"

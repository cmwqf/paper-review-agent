"""Purpose: Tests for DeepReview-Bench dev CLI runner."""

from __future__ import annotations

from dataclasses import dataclass, field

from reviewer.cli import build_parser
from reviewer.cli import run_bench_dev
from reviewer.schemas.qa import QAResult, ReviewImpact
from reviewer.utils.jsonl import read_jsonl


@dataclass
class FakeState:
    summary_xml: str = "<paper_summary />"
    dimension_reviews: dict[str, str] = field(
        default_factory=lambda: {
            "Contribution": "<dimension_review><dimension>Contribution</dimension></dimension_review>",
            "Soundness": "<dimension_review><dimension>Soundness</dimension></dimension_review>",
            "Presentation": "<dimension_review><dimension>Presentation</dimension></dimension_review>",
        }
    )
    qa_trajectories: dict[str, list[QAResult]] = field(
        default_factory=lambda: {
            "Contribution": [
                QAResult(
                    question="Is the method novel?",
                    answer="Partially; the setting is useful but close to prior work.",
                    evidence=["paper: contribution paragraph"],
                    retrieved_papers=[
                        {
                            "title": "Prior Work",
                            "year": "2024",
                            "url": "https://example.com",
                            "relevance": "related baseline",
                        }
                    ],
                    review_impact=ReviewImpact(
                        dimension="Contribution",
                        polarity="weakness",
                        impact_level="C2",
                        confidence="medium",
                    ),
                )
            ]
        }
    )
    final_review_xml: str = "<final_review />"


class FakeWorkflow:
    instances = []

    def __init__(self, config):
        self.config = config
        self.__class__.instances.append(self)

    def run(self, paper):
        if paper["id"] == "bad":
            raise RuntimeError("model failed")
        return FakeState()


def test_run_bench_dev_writes_results_and_errors(tmp_path, monkeypatch):
    FakeWorkflow.instances = []
    split = tmp_path / "split.jsonl"
    split.write_text('{"id":"ok"}\n{"id":"bad"}\n', encoding="utf-8")

    monkeypatch.setattr(
        "reviewer.cli.load_bench_paper",
        lambda row, bench_root: {
            "id": row["id"],
            "title": row["id"],
            "metadata": {"decision": "Reject"},
        },
    )
    monkeypatch.setattr("reviewer.cli.ReviewWorkflow", FakeWorkflow)

    counts = run_bench_dev(
        config={},
        split_path=split,
        bench_root=tmp_path,
        output_dir=tmp_path / "out",
    )

    assert counts == {"processed": 1, "skipped": 0, "failed": 1}
    assert (tmp_path / "out" / "ok" / "summary.xml").read_text(encoding="utf-8") == "<paper_summary />"
    summary_debug = (tmp_path / "out" / "ok" / "summary.md").read_text(encoding="utf-8")
    assert "# Paper Map" in summary_debug
    assert "PAPER MAP" in summary_debug
    assert "<paper_summary" not in summary_debug
    assert (tmp_path / "out" / "ok" / "contribution.xml").exists()
    assert (tmp_path / "out" / "ok" / "qa_trajectory.json").exists()
    assert "Is the method novel?" in (tmp_path / "out" / "ok" / "qa_trajectory.md").read_text(
        encoding="utf-8"
    )
    assert (tmp_path / "out" / "ok" / "final_review.xml").exists()
    result = read_jsonl(tmp_path / "out" / "results.jsonl")[0]
    assert result["id"] == "ok"
    assert result["summary_xml"].endswith("summary.xml")
    assert result["summary_paper_map"].endswith("summary.md")
    assert read_jsonl(tmp_path / "out" / "errors.jsonl")[0]["id"] == "bad"


def test_run_bench_dev_resume_skips_completed(tmp_path, monkeypatch):
    FakeWorkflow.instances = []
    split = tmp_path / "split.jsonl"
    split.write_text('{"id":"done"}\n{"id":"new"}\n', encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    (out / "results.jsonl").write_text('{"id":"done"}\n', encoding="utf-8")

    loaded = []

    def fake_load(row, bench_root):
        loaded.append(row["id"])
        return {"id": row["id"], "title": row["id"], "metadata": {}}

    monkeypatch.setattr("reviewer.cli.load_bench_paper", fake_load)
    monkeypatch.setattr("reviewer.cli.ReviewWorkflow", FakeWorkflow)

    counts = run_bench_dev(
        config={},
        split_path=split,
        bench_root=tmp_path,
        output_dir=out,
        resume=True,
    )

    assert counts == {"processed": 1, "skipped": 1, "failed": 0}
    assert loaded == ["new"]


def test_run_bench_dev_supports_configured_concurrency(tmp_path, monkeypatch):
    FakeWorkflow.instances = []
    split = tmp_path / "split.jsonl"
    split.write_text('{"id":"a"}\n{"id":"b"}\n', encoding="utf-8")

    monkeypatch.setattr(
        "reviewer.cli.load_bench_paper",
        lambda row, bench_root: {
            "id": row["id"],
            "title": row["id"],
            "metadata": {"decision": "Reject"},
        },
    )
    monkeypatch.setattr("reviewer.cli.ReviewWorkflow", FakeWorkflow)

    counts = run_bench_dev(
        config={"bench": {"concurrency": 2}},
        split_path=split,
        bench_root=tmp_path,
        output_dir=tmp_path / "out",
    )

    assert counts == {"processed": 2, "skipped": 0, "failed": 0}
    assert len(read_jsonl(tmp_path / "out" / "results.jsonl")) == 2


def test_run_bench_dev_cli_uses_configured_paths_and_resumes_by_default():
    parser = build_parser()
    args = parser.parse_args(["run-bench-dev", "--limit", "1"])

    assert args.command == "run-bench-dev"
    assert args.limit == 1
    assert args.concurrency is None
    assert args.fresh is False
    assert not hasattr(args, "bench_root")
    assert not hasattr(args, "output")


def test_run_bench_dev_cli_supports_fresh_start():
    parser = build_parser()
    args = parser.parse_args(["run-bench-dev", "--fresh"])

    assert args.command == "run-bench-dev"
    assert args.fresh is True


def test_run_bench_dev_cli_supports_concurrency_override():
    parser = build_parser()
    args = parser.parse_args(["run-bench-dev", "--concurrency", "4"])

    assert args.command == "run-bench-dev"
    assert args.concurrency == 4

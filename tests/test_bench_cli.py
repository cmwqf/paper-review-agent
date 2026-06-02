"""Purpose: Tests for DeepReview-Bench dev CLI runner."""

from __future__ import annotations

from dataclasses import dataclass, field

from reviewer.cli import _load_cli_config, _resolve_bench_paths, build_parser
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
    args = parser.parse_args(["--split", "dev", "--limit", "1"])

    assert args.command is None
    assert args.split == "dev"
    assert args.agent is None
    assert args.profile is None
    assert args.limit == 1
    assert args.concurrency is None
    assert args.fresh is False
    assert not hasattr(args, "bench_root")
    assert not hasattr(args, "output")


def test_run_bench_dev_cli_supports_fresh_start():
    parser = build_parser()
    args = parser.parse_args(["--fresh"])

    assert args.command is None
    assert args.fresh is True


def test_run_bench_dev_cli_supports_concurrency_override():
    parser = build_parser()
    args = parser.parse_args(["--concurrency", "4"])

    assert args.command is None
    assert args.concurrency == 4


def test_cli_supports_agent_override() -> None:
    parser = build_parser()
    args = parser.parse_args(["--agent", "deepseek_v4_pro"])

    assert args.command is None
    assert args.agent == "deepseek_v4_pro"


def test_load_cli_config_applies_profile_override(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
models:
  default:
    model: default-model
    base_url: http://localhost:8000/v1
  profiles:
    deepseek_v4_pro:
      final_review:
        model: deepseek-v4-pro
""",
        encoding="utf-8",
    )
    parser = build_parser()
    args = parser.parse_args(["--config", str(config_path), "--agent", "deepseek_v4_pro"])

    config = _load_cli_config(args)

    assert config["model_profile"] == "deepseek_v4_pro"
    assert config["_selected_agent"] == "deepseek_v4_pro"


def test_resolve_bench_paths_uses_named_split_and_agent_output_dir(tmp_path) -> None:
    config = {
        "_selected_agent": "deepseek_v4_pro",
        "bench": {
            "root": str(tmp_path / "bench"),
            "output_dir": str(tmp_path / "outputs"),
            "splits": {
                "dev": str(tmp_path / "splits" / "dev.jsonl"),
            },
        },
    }

    split_path, bench_root, output_dir = _resolve_bench_paths(config, "dev")

    assert split_path == str(tmp_path / "splits" / "dev.jsonl")
    assert bench_root == str(tmp_path / "bench")
    assert output_dir == tmp_path / "outputs" / "dev_deepseek_v4_pro"

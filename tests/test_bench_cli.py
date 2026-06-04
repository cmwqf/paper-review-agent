"""Purpose: Tests for DeepReview-Bench dev CLI runner."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from reviewer.cli import (
    _load_cli_config,
    _paper_is_complete,
    _resolve_bench_paths,
    _resolve_run_output_dir,
    _reuse_source_dir,
    _set_run_log_file,
    _write_run_metrics,
    _write_review_artifacts,
    _write_run_metadata,
    build_parser,
)
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
            ],
            "Soundness": [],
            "Presentation": [],
        }
    )
    final_review_xml: str = "<final_review />"
    traces: dict[str, list[dict]] = field(
        default_factory=lambda: {
            "summary": [
                {
                    "event": "model_output",
                    "raw_output": "<paper_summary><metadata><title>Raw</title></metadata></paper_summary>",
                }
            ],
            "Contribution.answer_agent": [
                {
                    "event": "tool_observation",
                    "step": 1,
                    "dimension": "Contribution",
                    "question": "Is the method novel?",
                    "action": {"action": "search_file", "keyword": "novel"},
                    "observation": "search_file('novel') found line evidence.",
                }
            ],
        }
    )


class FakeWorkflow:
    instances = []

    def __init__(self, config):
        self.config = config
        self.__class__.instances.append(self)

    def run(self, paper, artifact_callback=None):
        if paper["id"] == "bad":
            raise RuntimeError("model failed")
        state = FakeState()
        if artifact_callback:
            artifact_callback(state)
        return state


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
    assert (
        tmp_path / "out" / "ok" / "xml" / "summary.xml"
    ).read_text(encoding="utf-8") == "<paper_summary />"
    summary_debug = (tmp_path / "out" / "ok" / "markdown" / "summary.md").read_text(
        encoding="utf-8"
    )
    assert "# Paper Map" in summary_debug
    assert "PAPER MAP" in summary_debug
    assert "<paper_summary" not in summary_debug
    assert (tmp_path / "out" / "ok" / "xml" / "contribution.xml").exists()
    assert (tmp_path / "out" / "ok" / "markdown" / "contribution.md").exists()
    assert (tmp_path / "out" / "ok" / "qa_trajectory.json").exists()
    assert "Is the method novel?" in (
        tmp_path / "out" / "ok" / "markdown" / "qa_trajectory.md"
    ).read_text(encoding="utf-8")
    assert (tmp_path / "out" / "ok" / "xml" / "final_review.xml").exists()
    assert (tmp_path / "out" / "ok" / "markdown" / "final_review.md").exists()
    assert "Final Review" in (
        tmp_path / "out" / "ok" / "markdown" / "final_review.md"
    ).read_text(encoding="utf-8")
    status = json.loads((tmp_path / "out" / "ok" / "status.json").read_text(encoding="utf-8"))
    assert status["complete"] is True
    assert status["stages"]["presentation_qa"] is True
    result = read_jsonl(tmp_path / "out" / "results.jsonl")[0]
    assert result["id"] == "ok"
    assert result["summary_xml"].endswith("xml/summary.xml")
    assert result["summary_paper_map"].endswith("markdown/summary.md")
    assert read_jsonl(tmp_path / "out" / "errors.jsonl")[0]["id"] == "bad"


def test_run_bench_dev_resume_skips_completed(tmp_path, monkeypatch):
    FakeWorkflow.instances = []
    split = tmp_path / "split.jsonl"
    split.write_text('{"id":"done"}\n{"id":"new"}\n', encoding="utf-8")
    out = tmp_path / "out"
    _write_review_artifacts(out / "done", FakeState())

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


def test_run_bench_dev_resume_uses_artifacts_not_results_jsonl(tmp_path, monkeypatch):
    FakeWorkflow.instances = []
    split = tmp_path / "split.jsonl"
    split.write_text('{"id":"done_without_files"}\n', encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    (out / "results.jsonl").write_text('{"id":"done_without_files"}\n', encoding="utf-8")

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

    assert counts == {"processed": 1, "skipped": 0, "failed": 0}
    assert loaded == ["done_without_files"]


def test_write_review_artifacts_marks_incomplete_until_all_stages_land(tmp_path):
    partial_state = FakeState(final_review_xml="")
    partial_state.dimension_reviews.pop("Presentation")

    _write_review_artifacts(tmp_path / "paper", partial_state)

    status = json.loads((tmp_path / "paper" / "status.json").read_text(encoding="utf-8"))
    assert status["complete"] is False
    assert status["stages"]["presentation"] is False
    assert _paper_is_complete(tmp_path / "paper") is False

    _write_review_artifacts(tmp_path / "paper", FakeState())

    status = json.loads((tmp_path / "paper" / "status.json").read_text(encoding="utf-8"))
    assert status["complete"] is True
    assert _paper_is_complete(tmp_path / "paper") is True


def test_trace_markdown_omits_raw_output_but_trace_json_keeps_it(tmp_path):
    _write_review_artifacts(tmp_path / "paper", FakeState())

    trace_md = (tmp_path / "paper" / "logs" / "trace.md").read_text(encoding="utf-8")
    trace_json = json.loads((tmp_path / "paper" / "logs" / "trace.json").read_text(encoding="utf-8"))

    assert "Raw Output" not in trace_md
    assert "<paper_summary><metadata><title>Raw</title></metadata></paper_summary>" not in trace_md
    assert "search_file('novel') found line evidence." in trace_md
    assert trace_json["summary"][0]["raw_output"].startswith("<paper_summary>")


def test_write_run_metrics_saves_outputs_inside_run_dir(tmp_path):
    run_dir = tmp_path / "runs" / "20260602_153012_GMT_dev_default"
    paper_dir = run_dir / "papers" / "paper-1"
    paper_dir.mkdir(parents=True)
    split = tmp_path / "split.jsonl"
    split.write_text(
        json.dumps(
            {
                "id": "paper-1",
                "decision": "Accept",
                "review": [
                    {
                        "content": {
                            "rating": "6",
                            "soundness": "3",
                            "presentation": "3",
                            "contribution": "3",
                        }
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "run_manifest.json").write_text(
        json.dumps({"split_path": str(split), "split": "dev", "agent": "default"}),
        encoding="utf-8",
    )
    xml_dir = paper_dir / "xml"
    xml_dir.mkdir(parents=True)
    (xml_dir / "final_review.xml").write_text(
        """
        <final_review>
          <final_score>6</final_score>
          <recommendation>Accept</recommendation>
        </final_review>
        """,
        encoding="utf-8",
    )
    for dimension, score in [
        ("contribution", 3),
        ("soundness", 3),
        ("presentation", 3),
    ]:
        (xml_dir / f"{dimension}.xml").write_text(
            f"<dimension_review><score>{score}</score></dimension_review>",
            encoding="utf-8",
        )

    result = _write_run_metrics(run_dir)

    assert result["status"] == "ok"
    assert (run_dir / "metrics" / "metrics.md").exists()
    assert (run_dir / "metrics" / "metrics.csv").exists()
    assert (run_dir / "metrics" / "metrics.json").exists()
    assert (run_dir / "metrics" / "details.jsonl").exists()
    assert (run_dir / "metrics" / "skipped.json").exists()
    assert not (run_dir.parent / "metrics.md").exists()
    assert "Rating MAE" in (run_dir / "metrics" / "metrics.md").read_text(encoding="utf-8")


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


def test_run_bench_dev_can_write_index_files_to_run_root(tmp_path, monkeypatch):
    FakeWorkflow.instances = []
    split = tmp_path / "split.jsonl"
    split.write_text('{"id":"ok"}\n', encoding="utf-8")

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
        output_dir=tmp_path / "run" / "papers",
        index_dir=tmp_path / "run",
    )

    assert counts == {"processed": 1, "skipped": 0, "failed": 0}
    assert (tmp_path / "run" / "results.jsonl").exists()
    assert not (tmp_path / "run" / "papers" / "results.jsonl").exists()
    assert (tmp_path / "run" / "papers" / "ok" / "xml" / "summary.xml").exists()


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


def test_cli_supports_reuse_from() -> None:
    parser = build_parser()
    args = parser.parse_args(["--reuse-from", "outputs/deepreview_bench/dev"])

    assert args.command is None
    assert args.reuse_from == "outputs/deepreview_bench/dev"


def test_cli_supports_resume_run_dir() -> None:
    parser = build_parser()
    args = parser.parse_args(["--resume", "outputs/deepreview_bench/runs/run"])

    assert args.command is None
    assert args.resume == "outputs/deepreview_bench/runs/run"


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


def test_resolve_bench_paths_uses_named_split_and_runs_base(tmp_path) -> None:
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

    split_path, bench_root, output_base = _resolve_bench_paths(config, "dev")

    assert split_path == str(tmp_path / "splits" / "dev.jsonl")
    assert bench_root == str(tmp_path / "bench")
    assert output_base == tmp_path / "outputs" / "runs"


def test_resolve_run_output_dir_creates_gmt_run_dir(tmp_path, monkeypatch) -> None:
    class FixedDatetime:
        @classmethod
        def now(cls, tz=None):
            from datetime import datetime

            return datetime(2026, 6, 2, 15, 30, 12, tzinfo=tz)

    monkeypatch.setattr("reviewer.cli.datetime", FixedDatetime)

    run_dir, papers_dir = _resolve_run_output_dir(
        config={"_selected_agent": "deepseek_v4_pro"},
        output_base=tmp_path / "runs",
        split_name="dev",
    )

    assert run_dir == tmp_path / "runs" / "20260602_153012_GMT_dev_deepseek_v4_pro"
    assert papers_dir == run_dir / "papers"
    assert papers_dir.exists()


def test_resolve_run_output_dir_resumes_existing_run(tmp_path) -> None:
    run_dir = tmp_path / "runs" / "existing"
    run_dir.mkdir(parents=True)

    resolved_run_dir, papers_dir = _resolve_run_output_dir(
        config={},
        output_base=tmp_path / "runs",
        split_name="dev",
        resume_dir=run_dir,
    )

    assert resolved_run_dir == run_dir
    assert papers_dir == run_dir / "papers"
    assert papers_dir.exists()


def test_reuse_source_dir_supports_run_and_legacy_layouts(tmp_path) -> None:
    run_dir = tmp_path / "run"
    (run_dir / "papers").mkdir(parents=True)
    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir()

    assert _reuse_source_dir(run_dir, "paper1") == run_dir / "papers" / "paper1"
    assert _reuse_source_dir(legacy_dir, "paper1") == legacy_dir / "paper1"


def test_set_run_log_file_routes_logs_to_run_dir(tmp_path) -> None:
    config = {"logging": {"level": "INFO", "log_file": "outputs/logs/reviewer.log"}}
    run_dir = tmp_path / "run"

    _set_run_log_file(config, run_dir)

    assert config["logging"]["log_file"] == str(run_dir / "logs" / "reviewer.log")


def test_write_run_metadata_writes_manifest_and_config(tmp_path) -> None:
    parser = build_parser()
    args = parser.parse_args(["--split", "dev", "--agent", "deepseek_v4_pro", "--limit", "2"])
    run_dir = tmp_path / "run"
    papers_dir = run_dir / "papers"
    papers_dir.mkdir(parents=True)
    config = {
        "_selected_agent": "deepseek_v4_pro",
        "review": {"rubric_profile": "ICLR"},
        "bench": {"concurrency": 8},
        "logging": {"level": "INFO", "log_file": str(run_dir / "logs" / "reviewer.log")},
    }

    _write_run_metadata(
        run_dir=run_dir,
        config=config,
        args=args,
        split_path=tmp_path / "split.jsonl",
        bench_root=tmp_path / "bench",
        papers_output_dir=papers_dir,
    )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["split"] == "dev"
    assert manifest["agent"] == "deepseek_v4_pro"
    assert manifest["rubric_profile"] == "ICLR"
    assert manifest["limit"] == 2
    assert manifest["papers_output_dir"] == str(papers_dir)
    assert manifest["log_file"] == str(run_dir / "logs" / "reviewer.log")
    config_snapshot = (run_dir / "run_config.yaml").read_text(encoding="utf-8")
    assert "_selected_agent" not in config_snapshot
    assert "rubric_profile: ICLR" in config_snapshot
    assert f"log_file: {run_dir / 'logs' / 'reviewer.log'}" in config_snapshot

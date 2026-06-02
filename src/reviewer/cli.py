"""Purpose: Command-line entry points for running Reviewer workflows."""

from __future__ import annotations

import argparse
import json
import traceback
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import yaml
from tqdm.auto import tqdm

from reviewer.agents.contribution.agent import ContributionAgent
from reviewer.agents.dimension_base import _write_dimension_review
from reviewer.agents.final.agent import FinalReviewAgent
from reviewer.agents.presentation.agent import PresentationAgent
from reviewer.agents.soundness.agent import SoundnessAgent
from reviewer.agents.summary.agent import SummaryAgent
from reviewer.models.factory import build_llm
from reviewer.logging import configure_logging
from reviewer.paper.bench_loader import load_bench_paper, load_bench_split
from reviewer.paper.loader import load_paper
from reviewer.schemas.qa import QAResult
from reviewer.schemas.summary import parse_summary_xml, render_summary_for_agent
from reviewer.settings import load_config
from reviewer.utils.jsonl import append_jsonl
from reviewer.utils.io import write_json, write_text
from reviewer.workflow.review_workflow import ReviewWorkflow
from reviewer.workflow.state import ReviewWorkflowState

_DIMENSION_NAMES = ("Contribution", "Soundness", "Presentation")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without executing workflow code."""
    parser = argparse.ArgumentParser(prog="reviewer")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--agent",
        default=None,
        help="Optional models.profiles key to apply for this run.",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--split",
        default="dev",
        help="Configured benchmark split name, such as dev, lite, test, or all.",
    )
    parser.add_argument("--start", type=int, default=0, help="Start row index in the split.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of rows to process.")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Override bench.concurrency for concurrent paper runs.",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore existing per-paper artifacts and process rows from scratch.",
    )
    parser.add_argument(
        "--resume",
        default=None,
        help="Existing run directory to continue. New runs create a GMT timestamped directory.",
    )
    parser.add_argument(
        "--reuse-from",
        default=None,
        help=(
            "Existing benchmark output directory to reuse summary.xml and "
            "qa_trajectory.json from; only rerun dimension summaries and final review."
        ),
    )

    subparsers = parser.add_subparsers(dest="command")
    summarize = subparsers.add_parser("summarize", help="Generate summary XML and paper-map markdown.")
    summarize.add_argument("--input", required=True, help="Path to JSONL, JSON, txt, md, or tex input.")
    summarize.add_argument("--index", type=int, default=0, help="Zero-based JSONL row index.")
    summarize.add_argument("--output", default=None, help="Optional output XML path.")
    summarize.add_argument("--json-output", default=None, help="Optional parsed summary JSON path.")

    run = subparsers.add_parser("run", help="Run review workflow for one paper.")
    run.add_argument("--paper", required=True, help="Path to a PDF or text paper.")

    batch = subparsers.add_parser("batch", help="Run review workflow for a JSONL batch.")
    batch.add_argument("--input", required=True, help="Path to input JSONL.")

    return parser


def main() -> None:
    """Parse CLI arguments; implementation will call workflow modules later."""
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "summarize":
        config = _load_cli_config(args)
        configure_logging(config)
        paper = load_paper(args.input, index=args.index)
        summary_xml = SummaryAgent(config).run(paper)
        output_path = args.output
        if output_path is None:
            output_dir = Path(config.get("project", {}).get("output_dir", "outputs")) / "summaries"
            output_path = output_dir / f"{paper['id']}.xml"
        write_text(output_path, summary_xml)
        write_text(Path(output_path).with_suffix(".md"), _summary_paper_map_markdown(summary_xml))
        json_output = args.json_output
        if json_output:
            summary = parse_summary_xml(summary_xml)
            write_json(json_output, summary.model_dump(exclude={"raw_xml"}, exclude_none=True))
        print(output_path)
        if json_output:
            print(json_output)
        return

    if args.command == "run":
        config = _load_cli_config(args)
        configure_logging(config)
        paper = load_paper(args.paper)
        output_dir = Path(config.get("project", {}).get("output_dir", "outputs")) / "reviews" / paper["id"]
        state = ReviewWorkflow(config).run(
            paper,
            artifact_callback=lambda current_state: _write_review_artifacts(output_dir, current_state),
        )
        _write_review_artifacts(output_dir, state)
        print(output_dir)
        return

    if args.command is None:
        config = _load_cli_config(args)
        split_path, bench_root, output_base = _resolve_bench_paths(config, args.split)
        run_dir, papers_output_dir = _resolve_run_output_dir(
            config=config,
            output_base=output_base,
            split_name=args.split,
            resume_dir=args.resume,
        )
        _set_run_log_file(config, run_dir)
        configure_logging(config)
        _write_run_metadata(
            run_dir=run_dir,
            config=config,
            args=args,
            split_path=split_path,
            bench_root=bench_root,
            papers_output_dir=papers_output_dir,
        )
        run_bench_dev(
            config=config,
            split_path=split_path,
            bench_root=bench_root,
            output_dir=papers_output_dir,
            index_dir=run_dir,
            start=args.start,
            limit=args.limit,
            resume=not args.fresh,
            concurrency=args.concurrency,
            reuse_from=args.reuse_from,
        )
        print(run_dir)
        return

    raise NotImplementedError(f"Command is scaffolded but not implemented yet: {args}")


def _load_cli_config(args: argparse.Namespace) -> dict:
    """Load config.yaml and apply command-line model profile overrides."""
    config = load_config(args.config)
    selected_agent = getattr(args, "agent", None) or getattr(args, "profile", None)
    if selected_agent:
        config["model_profile"] = selected_agent
        config["_selected_agent"] = selected_agent
    return config


def _resolve_bench_paths(config: dict, split_name: str) -> tuple[str | Path, str | Path, Path]:
    """Resolve a named benchmark split and its run output base directory."""
    bench_config = config.get("bench", {}) if isinstance(config.get("bench"), dict) else {}
    bench_root = bench_config.get("root")
    if not bench_root:
        raise ValueError("bench.root must be set in config.yaml.")

    splits = bench_config.get("splits", {}) if isinstance(bench_config.get("splits"), dict) else {}
    split_path = splits.get(split_name) or bench_config.get(f"{split_name}_split")
    if not split_path:
        raise ValueError(f"bench.splits.{split_name} must be set in config.yaml.")

    output_base = Path(bench_config.get("output_dir", "outputs/deepreview_bench")) / "runs"

    return split_path, bench_root, output_base


def _resolve_run_output_dir(
    *,
    config: dict,
    output_base: str | Path,
    split_name: str,
    resume_dir: str | Path | None = None,
) -> tuple[Path, Path]:
    """Resolve a new or resumed run directory and its paper output directory."""
    if resume_dir:
        run_dir = Path(resume_dir)
        if not run_dir.exists():
            raise FileNotFoundError(f"--resume run directory does not exist: {run_dir}")
        return run_dir, _papers_output_dir(run_dir)

    run_dir = _new_run_dir(Path(output_base), split_name, _agent_label(config))
    return run_dir, _papers_output_dir(run_dir)


def _new_run_dir(output_base: Path, split_name: str, agent_label: str) -> Path:
    """Create a unique GMT timestamped run directory."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_GMT")
    base_name = f"{timestamp}_{_slug(split_name)}_{_slug(agent_label)}"
    output_base.mkdir(parents=True, exist_ok=True)
    candidate = output_base / base_name
    suffix = 2
    while candidate.exists():
        candidate = output_base / f"{base_name}_{suffix}"
        suffix += 1
    candidate.mkdir(parents=True)
    return candidate


def _papers_output_dir(run_dir: Path) -> Path:
    """Return the directory containing per-paper artifacts for a run."""
    papers_dir = run_dir / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)
    return papers_dir


def _agent_label(config: dict) -> str:
    """Return the selected agent profile label for run naming."""
    return str(config.get("_selected_agent") or config.get("model_profile") or "default")


def _slug(value: str) -> str:
    """Make a compact filesystem-friendly label."""
    cleaned = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in str(value))
    return cleaned.strip("_") or "default"


def _write_run_metadata(
    *,
    run_dir: Path,
    config: dict,
    args: argparse.Namespace,
    split_path: str | Path,
    bench_root: str | Path,
    papers_output_dir: Path,
) -> None:
    """Persist run manifest and resolved config snapshot."""
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.exists():
        manifest = {
            "run_dir": str(run_dir),
            "papers_output_dir": str(papers_output_dir),
            "results_path": str(run_dir / "results.jsonl"),
            "errors_path": str(run_dir / "errors.jsonl"),
            "log_file": str(run_dir / "logs" / "reviewer.log"),
            "created_at_gmt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "split": args.split,
            "split_path": str(split_path),
            "bench_root": str(bench_root),
            "agent": _agent_label(config),
            "rubric_profile": config.get("review", {}).get("rubric_profile", "ICLR"),
            "start": args.start,
            "limit": args.limit,
            "concurrency": args.concurrency,
            "fresh": bool(args.fresh),
            "reuse_from": args.reuse_from,
            "resume": args.resume,
        }
        write_json(manifest_path, manifest)
    config_snapshot_path = run_dir / "run_config.yaml"
    if not config_snapshot_path.exists():
        serializable_config = {
            key: value for key, value in config.items() if not str(key).startswith("_")
        }
        write_text(config_snapshot_path, yaml.safe_dump(serializable_config, sort_keys=False))


def _set_run_log_file(config: dict, run_dir: Path) -> None:
    """Route benchmark logging to the current run directory."""
    logging_config = config.setdefault("logging", {})
    if isinstance(logging_config, dict):
        logging_config["log_file"] = str(run_dir / "logs" / "reviewer.log")



def run_bench_dev(
    *,
    config: dict,
    split_path: str | Path,
    bench_root: str | Path,
    output_dir: str | Path,
    start: int = 0,
    limit: int | None = None,
    resume: bool = False,
    concurrency: int | None = None,
    reuse_from: str | Path | None = None,
    index_dir: str | Path | None = None,
) -> dict[str, int]:
    """Run ReviewWorkflow over a DeepReview-Bench split."""
    rows = load_bench_split(split_path)
    selected = rows[start:]
    if limit is not None:
        selected = selected[:limit]

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    index_path = Path(index_dir) if index_dir is not None else output_path
    index_path.mkdir(parents=True, exist_ok=True)
    results_path = index_path / "results.jsonl"
    errors_path = index_path / "errors.jsonl"
    completed_ids = _completed_paper_ids(selected, output_path, start=start) if resume else set()
    pending = [
        (offset, row)
        for offset, row in enumerate(selected, start=start)
        if str(row.get("id") or f"row-{offset}") not in completed_ids
    ]
    if concurrency is None:
        concurrency = int(config.get("bench", {}).get("concurrency", 1))
    concurrency = max(1, int(concurrency))
    counts = {"processed": 0, "skipped": len(selected) - len(pending), "failed": 0}

    progress = tqdm(
        pending,
        total=len(selected),
        initial=counts["skipped"],
        desc="benchmark",
        unit="paper",
    )
    progress.set_postfix(
        processed=counts["processed"],
        skipped=counts["skipped"],
        failed=counts["failed"],
        refresh=False,
    )
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(
                _run_one_bench_paper,
                config,
                bench_root,
                output_path,
                offset,
                row,
                reuse_from,
                resume,
            ): (
                offset,
                row,
            )
            for offset, row in pending
        }
        for future in as_completed(futures):
            result = future.result()
            progress.update(1)
            progress.set_postfix_str(result["id"])
            if result["status"] == "processed":
                append_jsonl(results_path, result["row"])
                counts["processed"] += 1
            else:
                append_jsonl(errors_path, result["row"])
                counts["failed"] += 1
            progress.set_postfix(
                processed=counts["processed"],
                skipped=counts["skipped"],
                failed=counts["failed"],
                refresh=False,
            )
    progress.close()
    return counts


def _run_one_bench_paper(
    config: dict,
    bench_root: str | Path,
    output_path: Path,
    offset: int,
    row: dict,
    reuse_from: str | Path | None = None,
    resume: bool = False,
) -> dict:
    """Run and persist artifacts for one DeepReview-Bench paper."""
    paper_id = str(row.get("id") or f"row-{offset}")
    paper_output_dir = output_path / paper_id
    try:
        paper = load_bench_paper(row, bench_root)
        if reuse_from:
            state = _run_summary_only_from_artifacts(
                config,
                paper,
                _reuse_source_dir(Path(reuse_from), paper_id),
                output_dir=paper_output_dir,
            )
        elif resume and paper_output_dir.exists():
            state = _run_workflow_from_artifacts(config, paper, paper_output_dir)
        else:
            state = ReviewWorkflow(config).run(
                paper,
                artifact_callback=lambda current_state: _write_review_artifacts(
                    paper_output_dir,
                    current_state,
                ),
            )
        _write_review_artifacts(paper_output_dir, state)
        return {
            "status": "processed",
            "id": paper_id,
            "row": {
                "id": paper_id,
                "split_index": offset,
                "title": paper.get("title"),
                "decision": paper.get("metadata", {}).get("decision"),
                "output_dir": str(paper_output_dir),
                "summary_xml": str(paper_output_dir / "summary.xml"),
                "summary_paper_map": str(paper_output_dir / "summary.md"),
                "final_review_xml": str(paper_output_dir / "final_review.xml"),
            },
        }
    except Exception as exc:
        return {
            "status": "failed",
            "id": paper_id,
            "row": {
                "id": paper_id,
                "split_index": offset,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        }


def _reuse_source_dir(reuse_from: Path, paper_id: str) -> Path:
    """Resolve reused per-paper artifact directory from old or run-based layouts."""
    if (reuse_from / "papers").is_dir():
        return reuse_from / "papers" / paper_id
    return reuse_from / paper_id


def _run_workflow_from_artifacts(
    config: dict,
    paper: dict,
    output_dir: Path,
) -> ReviewWorkflowState:
    """Resume one paper from already persisted stage artifacts."""
    state = ReviewWorkflowState(paper=paper)
    _load_existing_artifacts(output_dir, state)

    if not state.summary_xml:
        summary_agent = SummaryAgent(config)
        state.summary_xml = summary_agent.run(paper)
        state.traces["summary"] = getattr(summary_agent, "trace_events", [])
        _write_review_artifacts(output_dir, state)

    regenerated_dimension = False
    for agent in [
        ContributionAgent(config),
        SoundnessAgent(config),
        PresentationAgent(config),
    ]:
        dimension = agent.dimension.value
        if state.dimension_reviews.get(dimension) and dimension in state.qa_trajectories:
            continue
        review_xml, qa_results = agent.run_with_qa(paper, state.summary_xml)
        state.dimension_reviews[dimension] = review_xml
        state.qa_trajectories[dimension] = qa_results
        state.traces[f"{dimension}.dimension_agent"] = getattr(agent, "trace_events", [])
        answer_events = []
        for result in qa_results:
            answer_events.extend(getattr(result, "trace_events", []))
        state.traces[f"{dimension}.answer_agent"] = answer_events
        regenerated_dimension = True
        _write_review_artifacts(output_dir, state)

    if (
        regenerated_dimension
        or not state.final_review_xml
        or not _all_stages_complete(_state_stage_status(state))
    ):
        final_agent = FinalReviewAgent(config)
        state.final_review_xml = final_agent.run(state.summary_xml, state.dimension_reviews)
        state.traces["final_review"] = getattr(final_agent, "trace_events", [])
        _write_review_artifacts(output_dir, state)

    return state


def _load_existing_artifacts(output_dir: Path, state: ReviewWorkflowState) -> None:
    """Load usable artifacts from a previous partial run into workflow state."""
    summary_xml = _read_stage_xml(output_dir / "summary.xml", "paper_summary")
    if summary_xml:
        state.summary_xml = summary_xml

    qa_payload = _read_json_object(output_dir / "qa_trajectory.json")
    for dimension in _DIMENSION_NAMES:
        review_xml = _read_stage_xml(output_dir / f"{dimension.lower()}.xml", "dimension_review")
        if review_xml:
            state.dimension_reviews[dimension] = review_xml
        if isinstance(qa_payload.get(dimension), list):
            state.qa_trajectories[dimension] = _load_qa_results(qa_payload[dimension])

    traces = _read_json_object(output_dir / "logs" / "trace.json")
    if traces:
        state.traces.update(traces)

    final_xml = _read_stage_xml(output_dir / "final_review.xml", "final_review")
    if final_xml:
        state.final_review_xml = final_xml


def _run_summary_only_from_artifacts(
    config: dict,
    paper: dict,
    source_dir: Path,
    output_dir: Path | None = None,
) -> ReviewWorkflowState:
    """Reuse existing paper summary and Q&A trajectory; rerun dimension/final summaries."""
    summary_path = source_dir / "summary.xml"
    qa_path = source_dir / "qa_trajectory.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing reused summary XML: {summary_path}")
    if not qa_path.exists():
        raise FileNotFoundError(f"Missing reused Q&A trajectory: {qa_path}")

    state = ReviewWorkflowState(paper=paper)
    state.summary_xml = summary_path.read_text(encoding="utf-8")
    if output_dir:
        _write_review_artifacts(output_dir, state)
    summary = parse_summary_xml(state.summary_xml)
    paper_map = render_summary_for_agent(summary)
    qa_payload = json.loads(qa_path.read_text(encoding="utf-8"))

    dimensions = [
        ("Contribution", "contribution"),
        ("Soundness", "soundness"),
        ("Presentation", "presentation"),
    ]
    for dimension, agent_name in dimensions:
        qa_results = _load_qa_results(qa_payload.get(dimension, []))
        model_key = config.get("agents", {}).get(agent_name, {}).get("model", "agent")
        client = build_llm(config, model_key)
        review_xml = _write_dimension_review(
            client=client,
            config=config,
            dimension=dimension,
            paper_map=paper_map,
            qa_results=qa_results,
        )
        state.dimension_reviews[dimension] = review_xml
        state.qa_trajectories[dimension] = qa_results
        state.traces[f"{dimension}.dimension_summary"] = [
            {
                "agent": agent_name,
                "event": "reuse_qa_summary_regenerated",
                "dimension": dimension,
                "model_key": model_key,
                "qa_count": len(qa_results),
            }
        ]
        if output_dir:
            _write_review_artifacts(output_dir, state)

    final_agent = FinalReviewAgent(config)
    state.final_review_xml = final_agent.run(state.summary_xml, state.dimension_reviews)
    state.traces["final_review"] = getattr(final_agent, "trace_events", [])
    if output_dir:
        _write_review_artifacts(output_dir, state)
    return state


def _load_qa_results(items: list[dict]) -> list[QAResult]:
    """Load QAResult objects from serialized qa_trajectory.json entries."""
    results = []
    for item in items:
        if hasattr(QAResult, "model_validate"):
            results.append(QAResult.model_validate(item))
        else:
            results.append(QAResult.parse_obj(item))
    return results


def _write_review_artifacts(output_dir: Path, state) -> None:
    """Persist workflow XML artifacts for one paper."""
    write_text(output_dir / "summary.xml", state.summary_xml or "")
    write_text(output_dir / "summary.md", _summary_paper_map_markdown(state.summary_xml or ""))
    for dimension, review_xml in state.dimension_reviews.items():
        write_text(output_dir / f"{dimension.lower()}.xml", review_xml)
    write_json(output_dir / "qa_trajectory.json", _qa_trajectories_payload(state))
    write_text(output_dir / "qa_trajectory.md", _qa_trajectories_markdown(state))
    write_json(output_dir / "logs" / "trace.json", getattr(state, "traces", {}))
    write_text(output_dir / "logs" / "trace.md", _trace_markdown(state))
    write_text(output_dir / "final_review.xml", state.final_review_xml or "")
    _write_paper_status(output_dir, state)


def _write_paper_status(output_dir: Path, state) -> None:
    """Persist per-paper completion status for artifact-based resume."""
    stages = _state_stage_status(state)
    write_json(
        output_dir / "status.json",
        {
            "id": str(getattr(state, "paper", {}).get("id", output_dir.name)),
            "updated_at_gmt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "stages": stages,
            "complete": _all_stages_complete(stages),
        },
    )


def _state_stage_status(state) -> dict[str, bool]:
    """Return stage completion flags from in-memory workflow state."""
    stages = {"summary": bool(getattr(state, "summary_xml", None))}
    dimension_reviews = getattr(state, "dimension_reviews", {})
    qa_trajectories = getattr(state, "qa_trajectories", {})
    for dimension in _DIMENSION_NAMES:
        key = dimension.lower()
        stages[key] = bool(dimension_reviews.get(dimension))
        stages[f"{key}_qa"] = dimension in qa_trajectories
    stages["final_review"] = bool(getattr(state, "final_review_xml", None))
    return stages


def _completed_paper_ids(rows: list[dict], output_path: Path, *, start: int) -> set[str]:
    """Return row ids whose per-paper artifacts show completed reviews."""
    completed = set()
    for offset, row in enumerate(rows, start=start):
        paper_id = str(row.get("id") or f"row-{offset}")
        if _paper_is_complete(output_path / paper_id):
            completed.add(paper_id)
    return completed


def _paper_is_complete(paper_dir: Path) -> bool:
    """Return whether a paper has all required landed artifacts."""
    return _all_stages_complete(_artifact_stage_status(paper_dir))


def _artifact_stage_status(paper_dir: Path) -> dict[str, bool]:
    """Infer stage completion from artifact files for old runs without status.json."""
    stages = {"summary": _stage_xml_exists(paper_dir / "summary.xml", "paper_summary")}
    qa_payload = _read_json_object(paper_dir / "qa_trajectory.json")
    for dimension in _DIMENSION_NAMES:
        key = dimension.lower()
        stages[key] = _stage_xml_exists(paper_dir / f"{key}.xml", "dimension_review")
        stages[f"{key}_qa"] = isinstance(qa_payload.get(dimension), list)
    stages["final_review"] = _stage_xml_exists(paper_dir / "final_review.xml", "final_review")
    return stages


def _all_stages_complete(stages: dict[str, bool]) -> bool:
    """Return whether all required paper review stages are marked complete."""
    required = ["summary", "final_review"]
    for dimension in _DIMENSION_NAMES:
        required.extend([dimension.lower(), f"{dimension.lower()}_qa"])
    return all(bool(stages.get(stage)) for stage in required)


def _read_stage_xml(path: Path, expected_root: str) -> str | None:
    """Read non-empty XML artifact if it has the expected root tag."""
    if not _stage_xml_exists(path, expected_root):
        return None
    return path.read_text(encoding="utf-8")


def _stage_xml_exists(path: Path, expected_root: str) -> bool:
    """Return whether a stage XML file is present, non-empty, and root-valid."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return False
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return False
    return root.tag == expected_root


def _read_json_object(path: Path) -> dict:
    """Read a JSON object artifact, returning empty dict when absent or invalid."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _summary_paper_map_markdown(summary_xml: str) -> str:
    """Render the downstream paper map in a concise markdown artifact."""
    summary = parse_summary_xml(summary_xml)
    paper_map = render_summary_for_agent(summary)
    return f"# Paper Map\n\n```text\n{paper_map.rstrip()}\n```\n"


def _qa_trajectories_payload(state) -> dict:
    """Serialize Q&A trajectories for JSON artifact output."""
    payload = {}
    for dimension, qa_results in getattr(state, "qa_trajectories", {}).items():
        payload[dimension] = [
            result.model_dump(exclude_none=True, exclude={"trace_events"})
            if hasattr(result, "model_dump")
            else result
            for result in qa_results
        ]
    return payload


def _trace_markdown(state) -> str:
    """Render model/tool traces for one paper."""
    traces = getattr(state, "traces", {})
    if not traces:
        return "# Trace\n\nNo trace events recorded.\n"

    lines = ["# Trace", ""]
    for name, events in traces.items():
        lines.extend([f"## {name}", ""])
        if not events:
            lines.extend(["No events.", ""])
            continue
        for index, event in enumerate(events, 1):
            lines.extend([f"### Event {index}: {event.get('event', 'unknown')}", ""])
            for key in ["turn", "step", "dimension", "question"]:
                if key in event:
                    lines.append(f"- **{key}:** {event[key]}")
            if "action" in event:
                lines.extend(["", "**Action:**", "```text", str(event["action"]), "```"])
            if "raw_output" in event:
                lines.extend(["", "**Raw Output:**", "```xml", str(event["raw_output"]).rstrip(), "```"])
            if "observation" in event:
                lines.extend(
                    ["", "**Observation:**", "```text", str(event["observation"]).rstrip(), "```"]
                )
            if event.get("retrieved_papers"):
                lines.extend(["", "**Retrieved Papers:**"])
                for paper in event["retrieved_papers"]:
                    lines.append(f"- {paper}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _qa_trajectories_markdown(state) -> str:
    """Render Q&A trajectories for direct human inspection."""
    trajectories = getattr(state, "qa_trajectories", {})
    if not trajectories:
        return "# Q&A Trajectory\n\nNo Q&A results recorded.\n"

    lines = ["# Q&A Trajectory", ""]
    for dimension, qa_results in trajectories.items():
        lines.extend([f"## {dimension}", ""])
        if not qa_results:
            lines.extend(["No Q&A results.", ""])
            continue
        for index, result in enumerate(qa_results, 1):
            impact = result.review_impact
            lines.extend(
                [
                    f"### Q{index}",
                    "",
                    f"**Question:** {result.question}",
                    "",
                    f"**Answer:** {result.answer}",
                    "",
                    (
                        "**Impact:** "
                        f"{impact.polarity}, {impact.impact_level}, confidence={impact.confidence}"
                    ),
                    "",
                ]
            )
            if result.evidence:
                lines.append("**Evidence:**")
                lines.extend(f"- {item}" for item in result.evidence)
                lines.append("")
            if result.retrieved_papers:
                lines.append("**Retrieved Papers:**")
                for paper in result.retrieved_papers:
                    title = paper.get("title", "")
                    year = paper.get("year", "")
                    url = paper.get("url", "")
                    relevance = paper.get("relevance", "")
                    parts = [part for part in [title, str(year), url, relevance] if part]
                    lines.append(f"- {' | '.join(parts)}")
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    main()

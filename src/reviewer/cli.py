"""Purpose: Command-line entry points for running Reviewer workflows."""

from __future__ import annotations

import argparse
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from tqdm.auto import tqdm

from reviewer.agents.summary.agent import SummaryAgent
from reviewer.logging import configure_logging
from reviewer.paper.bench_loader import load_bench_paper, load_bench_split
from reviewer.paper.loader import load_paper
from reviewer.schemas.summary import parse_summary_xml, render_summary_for_agent
from reviewer.settings import load_config
from reviewer.utils.jsonl import append_jsonl, read_jsonl_ids
from reviewer.utils.io import write_json, write_text
from reviewer.workflow.review_workflow import ReviewWorkflow


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without executing workflow code."""
    parser = argparse.ArgumentParser(prog="reviewer")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml.")

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

    run_dev = subparsers.add_parser(
        "run-bench-dev",
        help="Run the configured DeepReview-Bench dev split.",
    )
    run_dev.add_argument("--start", type=int, default=0, help="Start row index in the dev split.")
    run_dev.add_argument("--limit", type=int, default=None, help="Maximum number of rows to process.")
    run_dev.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Override bench.concurrency for concurrent paper runs.",
    )
    run_dev.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore existing results.jsonl and process rows from scratch.",
    )

    return parser


def main() -> None:
    """Parse CLI arguments; implementation will call workflow modules later."""
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "summarize":
        config = load_config(args.config)
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
        config = load_config(args.config)
        configure_logging(config)
        paper = load_paper(args.paper)
        state = ReviewWorkflow(config).run(paper)
        output_dir = Path(config.get("project", {}).get("output_dir", "outputs")) / "reviews" / paper["id"]
        _write_review_artifacts(output_dir, state)
        print(output_dir)
        return

    if args.command == "run-bench-dev":
        config = load_config(args.config)
        configure_logging(config)
        bench_config = config.get("bench", {})
        split_path = bench_config.get("dev_split")
        bench_root = bench_config.get("root")
        output_dir = bench_config.get("dev_output_dir")
        if not split_path:
            raise ValueError("bench.dev_split must be set in config.yaml.")
        if not bench_root:
            raise ValueError("bench.root must be set in config.yaml.")
        if not output_dir:
            output_dir = (
                Path(config.get("project", {}).get("output_dir", "outputs"))
                / "deepreview_bench"
                / "dev"
            )
        run_bench_dev(
            config=config,
            split_path=split_path,
            bench_root=bench_root,
            output_dir=output_dir,
            start=args.start,
            limit=args.limit,
            resume=not args.fresh,
            concurrency=args.concurrency,
        )
        print(output_dir)
        return

    raise NotImplementedError(f"Command is scaffolded but not implemented yet: {args}")


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
) -> dict[str, int]:
    """Run ReviewWorkflow over a DeepReview-Bench split."""
    rows = load_bench_split(split_path)
    selected = rows[start:]
    if limit is not None:
        selected = selected[:limit]

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    results_path = output_path / "results.jsonl"
    errors_path = output_path / "errors.jsonl"
    completed_ids = read_jsonl_ids(results_path) if resume else set()
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
        desc="run-bench-dev",
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
            executor.submit(_run_one_bench_paper, config, bench_root, output_path, offset, row): (
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
) -> dict:
    """Run and persist artifacts for one DeepReview-Bench paper."""
    paper_id = str(row.get("id") or f"row-{offset}")
    try:
        paper = load_bench_paper(row, bench_root)
        state = ReviewWorkflow(config).run(paper)
        paper_output_dir = output_path / paper_id
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

"""Purpose: Command-line entry points for running Reviewer workflows."""

from __future__ import annotations

import argparse
from pathlib import Path

from reviewer.agents.summary.agent import SummaryAgent
from reviewer.logging import configure_logging
from reviewer.paper.loader import load_paper
from reviewer.schemas.summary import parse_summary_xml
from reviewer.settings import load_config
from reviewer.utils.io import write_json, write_text


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without executing workflow code."""
    parser = argparse.ArgumentParser(prog="reviewer")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml.")

    subparsers = parser.add_subparsers(dest="command")
    summarize = subparsers.add_parser("summarize", help="Generate summary XML for one paper.")
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
        config = load_config(args.config)
        configure_logging(config)
        paper = load_paper(args.input, index=args.index)
        summary_xml = SummaryAgent(config).run(paper)
        output_path = args.output
        if output_path is None:
            output_dir = Path(config.get("project", {}).get("output_dir", "outputs")) / "summaries"
            output_path = output_dir / f"{paper['id']}.xml"
        write_text(output_path, summary_xml)
        summary = parse_summary_xml(summary_xml)
        json_output = args.json_output
        if json_output is None:
            json_output = str(Path(output_path).with_suffix(".json"))
        write_json(json_output, summary.model_dump(exclude={"raw_xml"}))
        print(output_path)
        print(json_output)
        return

    raise NotImplementedError(f"Command is scaffolded but not implemented yet: {args}")


if __name__ == "__main__":
    main()

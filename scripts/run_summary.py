"""Purpose: Run Summary Agent on one paper input and save `<paper_summary>` XML."""

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
    """Build CLI parser for summary-only runs."""
    parser = argparse.ArgumentParser(description="Generate paper_summary XML.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml.")
    parser.add_argument("--input", required=True, help="Path to JSONL, JSON, txt, md, or tex input.")
    parser.add_argument("--index", type=int, default=0, help="Zero-based JSONL row index.")
    parser.add_argument("--output", default=None, help="Optional output XML path.")
    parser.add_argument("--json-output", default=None, help="Optional parsed summary JSON path.")
    return parser


def main() -> None:
    """Run the summary agent and write XML output."""
    args = build_parser().parse_args()
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


if __name__ == "__main__":
    main()

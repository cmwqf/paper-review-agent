#!/usr/bin/env python3
"""Evaluate one or more Reviewer run directories against DeepReview-Bench."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import xml.etree.ElementTree as ET
from itertools import combinations
from pathlib import Path
from typing import Any


# Fill this list when you want to run the script without command-line paths.
# Each item can be either a run root, e.g.
#   outputs/deepreview_bench/runs/20260602_153012_GMT_dev_default
# or a papers directory, e.g.
#   outputs/deepreview_bench/runs/20260602_153012_GMT_dev_default/papers
RUN_DIRS: list[str] = [
    "/root/autodl-tmp/review_agent/Reviewer/outputs/deepreview_bench/dev",
    "/root/autodl-tmp/review_agent/Reviewer/outputs/deepreview_bench/dev_deepseek_v4_pro"
]


DIMENSIONS = ("soundness", "presentation", "contribution")
NUMERIC_FIELDS = ("rating", "soundness", "presentation", "contribution")
DEFAULT_DISPLAY_FIELDS = (
    "Run",
    "Evaluated",
    "Rating MSE",
    "Rating MAE",
    "Rating Spearman",
    "Soundness MSE",
    "Soundness MAE",
    "Soundness Spearman",
    "Presentation MSE",
    "Presentation MAE",
    "Presentation Spearman",
    "Contribution MSE",
    "Contribution MAE",
    "Contribution Spearman",
    "Decision Accuracy",
    "Decision F1",
)
PAIRWISE_DISPLAY_FIELDS = (
    "Pairwise Rating Acc",
    "Pairwise Soundness Acc",
    "Pairwise Presentation Acc",
    "Pairwise Contribution Acc",
)


def repo_root() -> Path:
    """Return the Reviewer repo root."""
    return Path(__file__).resolve().parent


def workspace_root() -> Path:
    """Return the parent workspace containing DeepReview-Bench."""
    return repo_root().parent


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Read JSONL rows."""
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def parse_score_value(value: Any) -> float:
    """Parse numeric score values from numbers, lists, or strings."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, list) and value:
        return parse_score_value(value[0])
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        if match:
            return float(match.group(0))
    raise ValueError(f"Unsupported score value: {value!r}")


def normalize_decision(value: Any) -> str:
    """Normalize a review decision to accept/reject."""
    text = str(value or "").strip()
    first_line = text.splitlines()[0].strip().lower() if text else ""
    if first_line == "accept" or re.search(r"\baccept\b", first_line):
        return "accept"
    if first_line == "reject" or re.search(r"\breject\b", first_line):
        return "reject"
    return ""


def infer_decision_from_score(score: float) -> str:
    """Infer accept/reject from ICLR-style final score."""
    return "accept" if score >= 6 else "reject"


def text_of(root: ET.Element, tag: str) -> str:
    """Return concatenated text for the first tag occurrence."""
    elem = root.find(f".//{tag}")
    if elem is None:
        return ""
    return "".join(elem.itertext()).strip()


def parse_xml_file(path: str | Path) -> ET.Element:
    """Parse XML file, allowing extra wrapper text."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        return ET.fromstring(f"<root>{text}</root>")


def parse_prediction(paper_dir: str | Path) -> dict[str, Any]:
    """Parse Reviewer XML predictions for one paper directory."""
    paper_dir = Path(paper_dir)
    pred: dict[str, Any] = {}

    final_path = paper_dir / "final_review.xml"
    if final_path.exists():
        root = parse_xml_file(final_path)
        final_score = text_of(root, "final_score")
        if final_score:
            pred["rating"] = parse_score_value(final_score)
        recommendation = text_of(root, "recommendation")
        pred["decision"] = normalize_decision(recommendation)
        if not pred["decision"] and "rating" in pred:
            pred["decision"] = infer_decision_from_score(pred["rating"])

    for dim in DIMENSIONS:
        dim_path = paper_dir / f"{dim}.xml"
        if not dim_path.exists():
            continue
        root = parse_xml_file(dim_path)
        score = text_of(root, "score")
        if score:
            pred[dim] = parse_score_value(score)

    return pred


def load_source_rows(split_file: str | Path) -> dict[str, dict[str, Any]]:
    """Load split rows and their original DeepReview review rows."""
    rows_by_id: dict[str, dict[str, Any]] = {}
    source_cache: dict[str, list[dict[str, Any]]] = {}
    for split_row in read_jsonl(split_file):
        source_file = split_row.get("source_file")
        source_index = split_row.get("source_index")
        row = None
        if source_file and source_index is not None and Path(source_file).exists():
            if source_file not in source_cache:
                source_cache[source_file] = read_jsonl(source_file)
            source_rows = source_cache[source_file]
            if 0 <= int(source_index) < len(source_rows):
                row = source_rows[int(source_index)]
        if row is None:
            row = split_row
        row = {**row, "decision": row.get("decision", split_row.get("decision", ""))}
        rows_by_id[split_row["id"]] = row
    return rows_by_id


def resolve_output_dir(path: str | Path) -> Path:
    """Resolve a run root or papers directory to the papers output directory."""
    output_path = Path(path)
    if (output_path / "papers").is_dir():
        return output_path / "papers"
    return output_path


def run_root_from_output_dir(output_dir: str | Path) -> Path:
    """Return the run root for a papers directory or legacy output directory."""
    output_path = Path(output_dir)
    if output_path.name == "papers":
        return output_path.parent
    return output_path


def infer_split_name_from_run_name(name: str) -> str:
    """Infer split name from run names or legacy <split>_<agent> names."""
    match = re.match(r"^\d{8}_\d{6}_GMT_(?P<rest>.+)$", name)
    rest = match.group("rest") if match else name
    known = ("dev", "lite", "test", "all")
    for split in known:
        if rest == split or rest.startswith(f"{split}_"):
            return split
    return rest.split("_", 1)[0]


def infer_split_file(output_dir: str | Path) -> Path:
    """Infer the DeepReview-Bench split file for an output or run directory."""
    output_path = Path(output_dir)
    run_root = run_root_from_output_dir(output_path)
    manifest_path = run_root / "run_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        split_path = manifest.get("split_path")
        if split_path and Path(split_path).exists():
            return Path(split_path)

    split_name = infer_split_name_from_run_name(run_root.name)
    candidates = []
    bench_splits = workspace_root() / "DeepReview-Bench" / "splits"
    if split_name == "dev":
        candidates.append(bench_splits / "deepreview13k_test_dev.jsonl")
    elif split_name in {"lite", "test_lite"}:
        candidates.append(bench_splits / "deepreview13k_test_lite.jsonl")
    elif split_name == "test":
        candidates.append(bench_splits / "deepreview13k_test.jsonl")
    elif split_name == "all":
        candidates.append(bench_splits / "all.jsonl")
    candidates.append(bench_splits / f"deepreview13k_test_{split_name}.jsonl")
    candidates.append(bench_splits / f"{split_name}.jsonl")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Could not infer split file for {output_dir}. Pass --split-file explicitly."
    )


def human_targets(row: dict[str, Any]) -> dict[str, Any]:
    """Compute human-review proxy targets from DeepReview review rows."""
    reviews = row.get("review") or []
    targets: dict[str, Any] = {}
    for field in NUMERIC_FIELDS:
        values = []
        for review in reviews:
            try:
                if field == "rating":
                    raw = review.get("content", {}).get("rating", review.get("rating"))
                else:
                    raw = review.get("content", {}).get(field)
                values.append(parse_score_value(raw))
            except Exception:
                continue
        if values:
            targets[field] = statistics.fmean(values)
    targets["decision"] = normalize_decision(row.get("decision"))
    return targets


def mean(values: list[float]) -> float:
    """Mean with nan for empty input."""
    return statistics.fmean(values) if values else math.nan


def rankdata(values: list[float]) -> list[float]:
    """Return average ranks for ties."""
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def pearson(xs: list[float], ys: list[float]) -> float:
    """Compute Pearson correlation."""
    if len(xs) < 2:
        return math.nan
    x_mean = mean(xs)
    y_mean = mean(ys)
    x_diff = [x - x_mean for x in xs]
    y_diff = [y - y_mean for y in ys]
    denom = math.sqrt(sum(x * x for x in x_diff) * sum(y * y for y in y_diff))
    if denom == 0:
        return math.nan
    return sum(x * y for x, y in zip(x_diff, y_diff)) / denom


def spearman(xs: list[float], ys: list[float]) -> float:
    """Compute Spearman rank correlation."""
    return pearson(rankdata(xs), rankdata(ys))


def macro_f1(true_labels: list[int], pred_labels: list[int]) -> float:
    """Compute macro-F1 for binary labels."""
    scores = []
    for label in (0, 1):
        tp = sum(1 for t, p in zip(true_labels, pred_labels) if t == label and p == label)
        fp = sum(1 for t, p in zip(true_labels, pred_labels) if t != label and p == label)
        fn = sum(1 for t, p in zip(true_labels, pred_labels) if t == label and p != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return mean(scores)


def pairwise_acc(records: list[dict[str, Any]], field: str) -> float:
    """Pairwise ranking accuracy for one numeric field."""
    total = 0
    correct = 0
    true_key = f"true_{field}"
    pred_key = f"pred_{field}"
    for left, right in combinations(records, 2):
        total += 1
        if (left[true_key] > right[true_key]) == (left[pred_key] > right[pred_key]):
            correct += 1
    return correct / total if total else math.nan


def fmt(value: Any) -> str:
    """Format metric values for tables."""
    if isinstance(value, float) and math.isnan(value):
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def run_label(run_dir: str | Path) -> str:
    """Return a readable label for a run or papers directory."""
    run_root = run_root_from_output_dir(run_dir)
    manifest_path = run_root / "run_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        split = manifest.get("split")
        agent = manifest.get("agent")
        if split and agent:
            return f"{run_root.name} ({split}, {agent})"
    return run_root.name


def evaluate(output_dir: str | Path, split_file: str | Path) -> tuple[dict[str, str], list[dict[str, Any]], list[dict[str, str]]]:
    """Evaluate one output directory."""
    output_path = resolve_output_dir(output_dir)
    rows_by_id = load_source_rows(split_file)
    records = []
    skipped = []

    for paper_dir in sorted(output_path.iterdir()):
        if not paper_dir.is_dir():
            continue
        paper_id = paper_dir.name
        row = rows_by_id.get(paper_id)
        if row is None:
            skipped.append({"id": paper_id, "reason": "missing ground truth row"})
            continue
        pred = parse_prediction(paper_dir)
        target = human_targets(row)
        missing = [field for field in NUMERIC_FIELDS if field not in pred or field not in target]
        if "decision" not in pred or not pred["decision"] or not target.get("decision"):
            missing.append("decision")
        if missing:
            skipped.append({"id": paper_id, "reason": f"missing fields: {', '.join(missing)}"})
            continue
        records.append(
            {
                "id": paper_id,
                **{f"true_{field}": target[field] for field in NUMERIC_FIELDS},
                **{f"pred_{field}": pred[field] for field in NUMERIC_FIELDS},
                "true_decision": target["decision"],
                "pred_decision": pred["decision"],
            }
        )

    if not records:
        raise ValueError(f"No valid paper outputs found in {output_path}.")

    results: dict[str, str] = {
        "Run": run_label(output_path),
        "Output Dir": str(output_path),
        "Split File": str(split_file),
        "Total Output Dirs": str(sum(1 for p in output_path.iterdir() if p.is_dir())),
        "Evaluated": str(len(records)),
        "Skipped": str(len(skipped)),
    }

    for field, label in (
        ("rating", "Rating"),
        ("soundness", "Soundness"),
        ("presentation", "Presentation"),
        ("contribution", "Contribution"),
    ):
        diffs = [record[f"pred_{field}"] - record[f"true_{field}"] for record in records]
        true_values = [record[f"true_{field}"] for record in records]
        pred_values = [record[f"pred_{field}"] for record in records]
        results[f"{label} MSE"] = fmt(mean([diff * diff for diff in diffs]))
        results[f"{label} MAE"] = fmt(mean([abs(diff) for diff in diffs]))
        results[f"{label} Spearman"] = fmt(spearman(true_values, pred_values))

    true_decisions = [1 if record["true_decision"] == "accept" else 0 for record in records]
    pred_decisions = [1 if record["pred_decision"] == "accept" else 0 for record in records]
    results["Decision Accuracy"] = fmt(
        mean([float(t == p) for t, p in zip(true_decisions, pred_decisions)])
    )
    results["Decision F1"] = fmt(macro_f1(true_decisions, pred_decisions))

    for field, label in (
        ("rating", "Rating"),
        ("soundness", "Soundness"),
        ("presentation", "Presentation"),
        ("contribution", "Contribution"),
    ):
        results[f"Pairwise {label} Acc"] = fmt(pairwise_acc(records, field))

    return results, records, skipped


def display_fields(include_all: bool = False) -> tuple[str, ...]:
    """Return metric fields to display."""
    if include_all:
        return DEFAULT_DISPLAY_FIELDS + PAIRWISE_DISPLAY_FIELDS
    return DEFAULT_DISPLAY_FIELDS


def comparison_markdown(rows: list[dict[str, str]], include_all: bool = False) -> str:
    """Render rows as a Markdown comparison table."""
    if not rows:
        return ""
    fields = display_fields(include_all)
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(lines)


def write_csv(path: str | Path, rows: list[dict[str, str]], include_all: bool = False) -> None:
    """Write comparison CSV."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = display_fields(include_all)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_runs_file(path: str | Path) -> list[str]:
    """Read run directories from a plain text file."""
    return [
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate one or more Reviewer run directories. Put run paths in RUN_DIRS "
            "near the top of this file, pass paths as arguments, or use --runs-file."
        )
    )
    parser.add_argument(
        "run_dirs",
        nargs="*",
        help="Run roots or papers directories to evaluate.",
    )
    parser.add_argument(
        "--runs-file",
        help="Optional text file containing one run root or papers directory per line.",
    )
    parser.add_argument(
        "--split-file",
        help="DeepReview-Bench split JSONL. Defaults to manifest or run-name inference.",
    )
    parser.add_argument("--save-json", help="Optional path to save comparison metrics JSON.")
    parser.add_argument("--save-md", help="Optional path to save comparison Markdown.")
    parser.add_argument("--save-csv", help="Optional path to save comparison CSV.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all metrics, including Pairwise ranking accuracy columns.",
    )
    parser.add_argument(
        "--save-details-dir",
        help="Optional directory to save per-paper details and skipped lists per run.",
    )
    args = parser.parse_args()

    run_dirs = []
    if args.runs_file:
        run_dirs.extend(read_runs_file(args.runs_file))
    run_dirs.extend(args.run_dirs)
    if not run_dirs:
        run_dirs = list(RUN_DIRS)
    if not run_dirs:
        raise SystemExit(
            "No run directories provided. Fill RUN_DIRS in get_metric.py, pass run paths, "
            "or use --runs-file."
        )

    rows = []
    details_payload = {}
    for run_dir in run_dirs:
        split_file = Path(args.split_file) if args.split_file else infer_split_file(run_dir)
        results, records, skipped = evaluate(run_dir, split_file)
        rows.append(results)
        details_payload[results["Run"]] = {
            "records": records,
            "skipped": skipped,
            "output_dir": results["Output Dir"],
            "split_file": results["Split File"],
        }

    table = comparison_markdown(rows, include_all=args.all)
    print(table)

    if args.save_json:
        output_path = Path(args.save_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.save_md:
        output_path = Path(args.save_md)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(table + "\n", encoding="utf-8")
    if args.save_csv:
        write_csv(args.save_csv, rows, include_all=args.all)
    if args.save_details_dir:
        details_dir = Path(args.save_details_dir)
        details_dir.mkdir(parents=True, exist_ok=True)
        for run_name, payload in details_payload.items():
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", run_name).strip("_")
            with (details_dir / f"{safe_name}.details.jsonl").open("w", encoding="utf-8") as handle:
                for record in payload["records"]:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            (details_dir / f"{safe_name}.skipped.json").write_text(
                json.dumps(payload["skipped"], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()

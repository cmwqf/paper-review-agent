#!/usr/bin/env python3
"""Evaluate generated final reviews with ScholarPeer-style H-Max scoring."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import yaml
from tqdm.auto import tqdm

from reviewer.models.factory import build_llm
from reviewer.settings import load_config
from reviewer.tools.retrieval_tool import RetrievalTool


DIMENSIONS = (
    "Technical Accuracy",
    "Constructive Value",
    "Analytical Depth",
    "Novelty and Significance Assessment",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compute ScholarPeer Appendix H.1 H-Max scores.")
    parser.add_argument("run_dir", help="Reviewer benchmark run directory or its papers directory.")
    parser.add_argument("--config", default="config.yaml", help="Reviewer config path.")
    parser.add_argument("--bench-root", default=None, help="DeepReview-Bench root override.")
    parser.add_argument("--model-key", default="final_review", help="Config model key for judge calls.")
    parser.add_argument("--agent", "--profile", dest="profile", default=None, help="Model profile override.")
    parser.add_argument("--output-dir", default=None, help="Directory for H-Max outputs.")
    parser.add_argument("--start", type=int, default=0, help="Start offset among complete papers.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum papers to evaluate.")
    parser.add_argument("--concurrency", type=int, default=1, help="Concurrent paper evaluations.")
    parser.add_argument("--max-paper-chars", type=int, default=50000, help="Max chars from paper.md.")
    parser.add_argument("--max-review-chars", type=int, default=9000, help="Max chars per review text.")
    parser.add_argument("--max-summary-chars", type=int, default=5000, help="Max chars from summary.md fallback.")
    parser.add_argument("--resume", action="store_true", help="Skip papers already in hmax_papers.jsonl.")
    parser.add_argument("--dry-run", action="store_true", help="Only inspect inputs; do not call the model.")
    parser.add_argument(
        "--no-retrieval",
        dest="retrieval",
        action="store_false",
        help="Disable Semantic Scholar pre-retrieval for the Novelty dimension.",
    )
    parser.add_argument(
        "--max-retrieved",
        type=int,
        default=8,
        help="Max candidate prior-work papers injected into the judge prompt.",
    )
    parser.set_defaults(retrieval=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    config = load_config(repo_root / args.config)
    if args.profile:
        config["model_profile"] = args.profile

    run_dir = resolve_run_dir(args.run_dir)
    papers_dir = resolve_papers_dir(run_dir)
    bench_root = Path(args.bench_root or infer_bench_root(config, run_dir)).resolve()
    output_dir = Path(args.output_dir) if args.output_dir else run_dir / "metrics" / "hmax"
    output_dir.mkdir(parents=True, exist_ok=True)

    jobs = collect_jobs(
        papers_dir=papers_dir,
        bench_root=bench_root,
        max_paper_chars=args.max_paper_chars,
        max_review_chars=args.max_review_chars,
        max_summary_chars=args.max_summary_chars,
    )
    jobs = jobs[args.start :]
    if args.limit is not None:
        jobs = jobs[: args.limit]

    retrieval_enabled = bool(args.retrieval) and bool(
        config.get("retrieval", {}).get("enabled", True)
    )
    retrieval_tool = RetrievalTool(config) if retrieval_enabled else None

    manifest = {
        "protocol": "ScholarPeer Appendix H.1 H-Max Score",
        "run_dir": str(run_dir),
        "papers_dir": str(papers_dir),
        "bench_root": str(bench_root),
        "output_dir": str(output_dir),
        "model_key": args.model_key,
        "model_profile": config.get("model_profile"),
        "dimensions": list(DIMENSIONS),
        "num_papers": len(jobs),
        "dry_run": args.dry_run,
        "retrieval_enabled": retrieval_enabled,
        "max_retrieved": args.max_retrieved if retrieval_enabled else 0,
    }
    write_json(output_dir / "hmax_manifest.json", manifest)

    if args.dry_run:
        preview = [
            {
                "paper_id": job["paper_id"],
                "title": job["title"],
                "human_reviews": len(job["human_reviews"]),
                "paper_text_chars": len(job["paper_text"]),
                "final_review_chars": len(job["generated_review"]),
                "cutoff_date": job["cutoff_date"],
                "submission_date": job["submission_date"],
                "retrieval_queries": build_retrieval_queries(job) if retrieval_enabled else [],
            }
            for job in jobs
        ]
        write_json(output_dir / "hmax_dry_run.json", preview)
        print(f"Dry run OK: {len(jobs)} complete papers, output={output_dir}")
        return

    details_path = output_dir / "hmax_details.jsonl"
    papers_path = output_dir / "hmax_papers.jsonl"
    errors_path = output_dir / "hmax_errors.jsonl"
    if args.resume:
        completed_ids = read_completed_ids(papers_path)
        jobs = [job for job in jobs if job["paper_id"] not in completed_ids]
    else:
        for path in (details_path, papers_path, errors_path):
            if path.exists():
                path.unlink()

    paper_rows: list[dict[str, Any]] = []
    detail_rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        futures = {
            executor.submit(
                evaluate_paper,
                config,
                args.model_key,
                job,
                retrieval_tool,
                args.max_retrieved,
            ): job
            for job in jobs
        }
        for future in tqdm(as_completed(futures), total=len(futures), desc="H-Max"):
            job = futures[future]
            try:
                paper_result, detail_result = future.result()
            except Exception as exc:
                append_jsonl(
                    errors_path,
                    {
                        "paper_id": job["paper_id"],
                        "title": job["title"],
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )
                continue
            append_jsonl(papers_path, paper_result)
            append_jsonl(details_path, detail_result)
            paper_rows.append(paper_result)
            detail_rows.append(detail_result)

    if args.resume:
        paper_rows = read_jsonl(papers_path)
        detail_rows = read_jsonl(details_path)
    metrics = aggregate_metrics(paper_rows, detail_rows)
    metrics["error_count"] = len(read_jsonl(errors_path)) if errors_path.exists() else 0
    write_json(output_dir / "hmax_metrics.json", metrics)
    write_metrics_md(output_dir / "hmax_metrics.md", metrics)
    print(output_dir)


def collect_jobs(
    *,
    papers_dir: Path,
    bench_root: Path,
    max_paper_chars: int,
    max_review_chars: int,
    max_summary_chars: int,
) -> list[dict[str, Any]]:
    jobs = []
    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        status_path = paper_dir / "status.json"
        final_path = paper_dir / "markdown" / "final_review.md"
        if not status_path.exists() or not final_path.exists():
            continue
        status = json.loads(status_path.read_text(encoding="utf-8"))
        if not status.get("complete"):
            continue

        paper_id = paper_dir.name
        review_path = bench_root / "papers" / paper_id / "review.json"
        if not review_path.exists():
            continue
        source = json.loads(review_path.read_text(encoding="utf-8"))
        human_reviews = normalize_human_reviews(source)
        if not human_reviews:
            continue

        paper_md_path = bench_root / "papers" / paper_id / "paper.md"
        summary_path = paper_dir / "markdown" / "summary.md"
        if paper_md_path.exists():
            paper_text = read_text_limited(paper_md_path, max_paper_chars)
        elif summary_path.exists():
            paper_text = read_text_limited(summary_path, max_summary_chars)
        else:
            paper_text = ""

        metadata_path = bench_root / "papers" / paper_id / "metadata.json"
        paper_metadata = (
            json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
        )
        review_metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
        cutoff_date = (
            source.get("date")
            or review_metadata.get("date")
            or review_metadata.get("submission_date")
            or paper_metadata.get("date")
            or paper_metadata.get("submission_date")
            or "the paper submission date"
        )
        jobs.append(
            {
                "paper_id": paper_id,
                "title": source.get("title") or paper_id,
                "human_decision": normalize_decision(source.get("decision", "")),
                "cutoff_date": cutoff_date,
                "submission_date": iso_date_or_none(cutoff_date),
                "paper_text": paper_text,
                "generated_review": read_text_limited(final_path, max_review_chars),
                "human_reviews": [
                    {**review, "text": truncate(review["text"], max_review_chars)}
                    for review in human_reviews
                ],
            }
        )
    return jobs


def evaluate_paper(
    config: dict[str, Any],
    model_key: str,
    job: dict[str, Any],
    retrieval_tool: RetrievalTool | None = None,
    max_retrieved: int = 8,
) -> tuple[dict[str, Any], dict[str, Any]]:
    prior_work = retrieve_prior_work(retrieval_tool, job, max_retrieved)
    client = build_llm(config, model_key)
    raw = client.generate(
        [
            {"role": "system", "content": scholarpeer_hmax_system_prompt(job["cutoff_date"])},
            {
                "role": "user",
                "content": scholarpeer_hmax_user_prompt(
                    paper_text=job["paper_text"],
                    ai_review=job["generated_review"],
                    human_reviews=render_all_human_reviews(job["human_reviews"]),
                    prior_work=render_prior_work(prior_work, job["cutoff_date"]),
                ),
            },
        ]
    )
    parsed = parse_judge_json(raw)
    detail = normalize_evaluation(job, parsed, raw)
    detail["Retrieved Prior Work"] = prior_work
    paper_row = {
        "paper_id": job["paper_id"],
        "title": job["title"],
        "human_decision": job["human_decision"],
        "cutoff_date": job["cutoff_date"],
        "num_human_reviews": len(job["human_reviews"]),
        "hmax": detail["Overall Score"],
    }
    for dimension in DIMENSIONS:
        paper_row[_metric_key(dimension)] = detail[f"{dimension} Score"]
    return paper_row, detail


def normalize_evaluation(job: dict[str, Any], parsed: dict[str, Any], raw: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "paper_id": job["paper_id"],
        "title": job["title"],
        "cutoff_date": job["cutoff_date"],
        "num_human_reviews": len(job["human_reviews"]),
        "raw_output": raw,
    }
    for dimension in DIMENSIONS:
        row[f"{dimension} Reason"] = normalize_text(parsed.get(f"{dimension} Reason"))
        row[f"{dimension} Score"] = clamp_score_10(parsed.get(f"{dimension} Score"))
    row["Novelty and Significance Assessment External Sources Used"] = parsed.get(
        "Novelty and Significance Assessment External Sources Used", []
    )
    row["Overall Reason"] = normalize_text(parsed.get("Overall Reason"))
    row["Overall Score"] = clamp_score_10(parsed.get("Overall Score"))
    return row


def build_retrieval_queries(job: dict[str, Any]) -> list[str]:
    """Derive deterministic Semantic Scholar queries for the Novelty dimension."""
    queries: list[str] = []
    title = str(job.get("title") or "").strip()
    if title and title != job.get("paper_id"):
        queries.append(title)
    return queries


def retrieve_prior_work(
    retrieval_tool: RetrievalTool | None,
    job: dict[str, Any],
    max_retrieved: int,
) -> list[dict[str, Any]]:
    """Pre-retrieve time-filtered candidate prior work for novelty grounding."""
    if retrieval_tool is None or max_retrieved <= 0:
        return []
    paper_metadata = {"submission_date": job.get("submission_date")}
    seen: set[str] = set()
    collected: list[dict[str, Any]] = []
    for query in build_retrieval_queries(job):
        try:
            results = retrieval_tool.search(query, paper_metadata)
        except Exception:
            results = []
        for paper in results:
            key = (paper.get("url") or paper.get("title") or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            collected.append(paper)
            if len(collected) >= max_retrieved:
                return collected
    return collected


def render_prior_work(prior_work: list[dict[str, Any]], cutoff_date: str) -> str:
    """Render retrieved candidates as a citable list for the judge prompt."""
    if not prior_work:
        return (
            "No external candidates were retrieved. Rely only on your own knowledge "
            f"of work published on or before {cutoff_date}."
        )
    lines = []
    for index, paper in enumerate(prior_work, start=1):
        date = paper.get("publication_date") or paper.get("year") or "n.d."
        citations = paper.get("citation_count")
        header = f"[{index}] {paper.get('title') or 'Untitled'} ({date})"
        if citations is not None:
            header += f" — citations: {citations}"
        if paper.get("url"):
            header += f" — {paper['url']}"
        abstract = normalize_text(paper.get("abstract"))
        if abstract:
            abstract = truncate(abstract, 600)
            lines.append(f"{header}\n{abstract}")
        else:
            lines.append(header)
    return "\n\n".join(lines)


def iso_date_or_none(value: Any) -> str | None:
    """Return value as an ISO date string when it parses, else None."""
    text = str(value or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    return None


def scholarpeer_hmax_system_prompt(cutoff_date: str) -> str:
    """ScholarPeer Appendix H.1 H-Max judge prompt, adapted only for API formatting."""
    return f"""You are an expert area chair evaluating an AI Reviewer Assistant. Your role is to determine if the AI provides value beyond what expert human reviewers provided.

Special Instruction for evaluating "Novelty and Significance Assessment": You must only search for and consider information available on or before the cutoff date: {cutoff_date}. The cutoff date represents the date on which the paper was published; information after this date is irrelevant to the review.

To support this, you are given a pre-retrieved list of candidate prior work under "#### Retrieved Prior Work ####", obtained from Semantic Scholar and already filtered to papers published on or before {cutoff_date}. Treat this list as your external search results: ground your Novelty and Significance Assessment in it, and cite the specific entries you rely on in "Novelty and Significance Assessment External Sources Used". You may also draw on your own knowledge of work published on or before {cutoff_date}, but never rely on or cite anything published after it.

Follow the steps below for each evaluation:
1. Thoroughly understand the paper by analyzing:
- Research objectives and contributions
- Methodology and experiments
- Claims and evidence
- Results and conclusions
2. Identify the strongest points in the Human Reviews (collectively) to establish a standard expert baseline.
3. Identify the delta: What did the AI mention that the humans missed? What did the humans mention that the AI missed?
4. Verify the validity of each of the delta claims using direct quotes from the paper and external sources (for novelty and significance only).
5. Assess the value-add of the AI review compared to the best human review for each aspect.

You will evaluate reviews based on these key aspects:
**Technical Accuracy**
- How technically accurate is the AI review compared to the humans?
**Constructive Value**
- How actionable is the feedback compared to the humans?
**Analytical Depth**
- How thorough is the depth of AI review compared to humans?
**Novelty and Significance Assessment (Search encouraged)**
Use search to actively verify the reviewers' claims about novelty and significance.
1. Identify claims: What do the paper and reviewers claim is novel?
2. Formulate search queries: Create targeted queries to find relevant prior work for these specific claims, explicitly restricting results to before {cutoff_date}.
3. Execute Search: Focus on top-tier conferences in the relevant domain and arXiv.
4. Verify and Compare:
- Did the AI find prior work that limits novelty which the humans missed? (High Score)
- Did the AI claim "high novelty" when humans correctly identified it as derivative work? (Low Score)
- Which assessment aligns better with the actual state of the field at the time?
5. Cite Sources: You must cite the specific external papers (title, venue, year) you used to make this determination in the JSON output.

For each of the above aspects and overall judgment, you must:
1. Provide specific evidence from source materials
2. Quote directly from paper and reviews; external sources only for "Novelty and Significance Assessment"
3. Explain your reasoning in detail
4. Consider alternative interpretations

**Input Format:**
#### Paper Text: ####
<Paper text>
#### AI Assistant's Review: ####
<AI Review>
#### Human Reviews (Ground Truth): ####
<Human Reviews>
#### Retrieved Prior Work (published on or before the cutoff date): ####
<Candidate prior work from Semantic Scholar>

**Respond in the following format:**
THOUGHT:
<THOUGHT>
EVALUATION JSON:
```json
<JSON>
```

In <THOUGHT>, for each aspect, compare the AI Assistant's review against the set of Human Reviews. Identify the best human review for that specific aspect and use it as your baseline (Score = 5), as a standard expert. You must justify why the AI deserves a higher or lower score based on the "Value-Add" it provides.

Scoring Rubric (Compare against Best Human Baseline):
- 10 (Superhuman / Verdict-Changing): The AI uncovers a critical insight that changes the fate of the paper (e.g., finding a fatal math error humans missed OR identifying a profound theoretical connection that elevates a rejected paper to an acceptance).
- 9 (Transformative / Insightful): The AI provides a novel perspective that significantly reframes the paper's contribution. It might articulate the significance better than the authors did, or identify a missing baseline that reframes the results.
- 8 (Clearly Superior): The AI review is significantly more thorough, constructive, or better substantiated than the best human review. It offers deep questions or literature context that humans omitted.
- 7 (Superior): The AI review is noticeably deeper and more constructive than the best human review, though perhaps not "transformative."
- 6 (Slightly Better): The AI review is slightly more polished, better structured, or covers one extra minor point compared to the best human review.
- 5 (Equivalent / Human Level): The AI review is roughly equivalent in quality to the best human review. It covers the same major points with similar depth.
- 4 (Slightly Worse): The AI review is valid but generic. It misses the specific nuance or "sharpness" that the expert human provided.
- 3 (Worse): The AI review is valid but vague. It lacks detail and actionable feedback compared to the human (e.g., "Improve experiments" vs "Add dataset X").
- 2 (Failure - Superficial): The review is technically "safe" (no direct lies) but functionally useless. It is too short, focuses only on trivial formatting issues, or completely misses the core technical innovation.
- 1 (Failure - Critical Error/Hallucination): The AI makes a factual error about the paper (e.g., claims it uses Method A when it uses Method B) or cites non-existent papers. The review actively misleads the reader.

In <JSON>, provide the evaluation in JSON format with the following fields in the order:
- "Technical Accuracy Reason": "<detailed reason>".
- "Technical Accuracy Score": <int 1-10>.
- "Constructive Value Reason": "<detailed reason>".
- "Constructive Value Score": <int 1-10>.
- "Analytical Depth Reason": "<detailed reason>".
- "Analytical Depth Score": <int 1-10>.
- "Novelty and Significance Assessment External Sources Used": List of retrieved papers (include title, venue, year and authors for each paper).
- "Novelty and Significance Assessment Reason": "<detailed reason>".
- "Novelty and Significance Assessment Score": <int 1-10>.
- "Overall Reason": "<detailed reason>".
- "Overall Score": <int 1-10>.
This JSON will be automatically parsed, so ensure the format is precise and scores are integers."""


def scholarpeer_hmax_user_prompt(
    *, paper_text: str, ai_review: str, human_reviews: str, prior_work: str
) -> str:
    return f"""#### Paper Text: ####
{paper_text}

#### AI Assistant's Review: ####
{ai_review}

#### Human Reviews: ####
{human_reviews}

#### Retrieved Prior Work: ####
{prior_work}"""


def parse_judge_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    marker = "EVALUATION JSON:"
    if marker in text:
        text = text.split(marker, 1)[1].strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            return json.loads(match.group(0))
        raise


def normalize_human_reviews(source: dict[str, Any]) -> list[dict[str, Any]]:
    reviews = source.get("reviews") or source.get("review") or []
    normalized = []
    for index, review in enumerate(reviews):
        content = review.get("content") if isinstance(review.get("content"), dict) else review
        text = render_human_review(content)
        if not text.strip():
            continue
        normalized.append(
            {
                "human_review_id": str(review.get("id") or f"human_{index}"),
                "human_review_index": index,
                "human_rating": parse_score(content.get("rating", review.get("rating"))),
                "human_decision": decision_from_rating(content.get("rating", review.get("rating"))),
                "text": text,
            }
        )
    return normalized


def render_human_review(content: dict[str, Any]) -> str:
    fields = [
        ("Summary", content.get("summary")),
        ("Soundness", content.get("soundness")),
        ("Presentation", content.get("presentation")),
        ("Contribution", content.get("contribution")),
        ("Strengths", content.get("strengths")),
        ("Weaknesses", content.get("weakness") or content.get("weaknesses")),
        ("Questions", content.get("questions")),
        ("Suggestions", content.get("suggestions")),
        ("Rating", content.get("rating")),
        ("Confidence", content.get("confidence")),
    ]
    parts = []
    for label, value in fields:
        text = normalize_text(value)
        if text:
            parts.append(f"## {label}\n{text}")
    return "\n\n".join(parts)


def render_all_human_reviews(human_reviews: list[dict[str, Any]]) -> str:
    parts = []
    for review in human_reviews:
        header = (
            f"### Human Review {review['human_review_index']} "
            f"(id={review['human_review_id']}, rating={review['human_rating']})"
        )
        parts.append(f"{header}\n{review['text']}")
    return "\n\n".join(parts)


def aggregate_metrics(
    paper_rows: list[dict[str, Any]],
    detail_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "evaluated_papers": len(paper_rows),
        "evaluated_evaluations": len(detail_rows),
        "mean_hmax": mean_field(paper_rows, "hmax"),
        "median_hmax": median_field(paper_rows, "hmax"),
    }
    for dimension in DIMENSIONS:
        metrics[f"mean_{_metric_key(dimension)}"] = mean_field(paper_rows, _metric_key(dimension))
    metrics["hmax_histogram"] = histogram([row["hmax"] for row in paper_rows])
    return metrics


def resolve_run_dir(path: str | Path) -> Path:
    path = Path(path).resolve()
    return path.parent if path.name == "papers" else path


def resolve_papers_dir(run_dir: Path) -> Path:
    papers_dir = run_dir / "papers"
    return papers_dir if papers_dir.is_dir() else run_dir


def infer_bench_root(config: dict[str, Any], run_dir: Path) -> str:
    manifest_path = run_dir / "run_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("bench_root"):
            return str(manifest["bench_root"])
    bench_root = config.get("bench", {}).get("root")
    if bench_root:
        return str(bench_root)
    return str(run_dir.parents[3] / "DeepReview-Bench")


def read_completed_ids(path: Path) -> set[str]:
    return {str(row.get("paper_id")) for row in read_jsonl(path) if row.get("paper_id")}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def mean_field(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows if is_number(row.get(key))]
    return round(statistics.fmean(values), 4) if values else math.nan


def median_field(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows if is_number(row.get(key))]
    return round(statistics.median(values), 4) if values else math.nan


def histogram(values: list[float]) -> dict[str, int]:
    bins = {"[1,3)": 0, "[3,5)": 0, "[5,7)": 0, "[7,9)": 0, "[9,10]": 0}
    for value in values:
        if not is_number(value):
            continue
        value = float(value)
        if value < 3:
            bins["[1,3)"] += 1
        elif value < 5:
            bins["[3,5)"] += 1
        elif value < 7:
            bins["[5,7)"] += 1
        elif value < 9:
            bins["[7,9)"] += 1
        else:
            bins["[9,10]"] += 1
    return bins


def write_metrics_md(path: Path, metrics: dict[str, Any]) -> None:
    lines = ["# H-Max Metrics", ""]
    for key, value in metrics.items():
        lines.append(f"- **{key}**: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_text_limited(path: Path, max_chars: int) -> str:
    return truncate(path.read_text(encoding="utf-8"), max_chars)


def truncate(text: str, max_chars: int) -> str:
    text = str(text or "")
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n\n[...truncated...]\n\n" + text[-half:]


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(normalize_text(item) for item in value if normalize_text(item))
    if isinstance(value, dict):
        return yaml.safe_dump(value, allow_unicode=True, sort_keys=False)
    return str(value).strip()


def parse_score(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value or ""))
    return float(match.group(0)) if match else None


def decision_from_rating(value: Any) -> str:
    score = parse_score(value)
    if score is None:
        return ""
    return "accept" if score >= 6 else "reject"


def normalize_decision(value: Any) -> str:
    text = str(value or "").lower()
    if "accept" in text:
        return "accept"
    if "reject" in text:
        return "reject"
    return ""


def clamp_score_10(value: Any) -> int | float:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        return math.nan
    return max(1, min(10, score))


def _metric_key(dimension: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", dimension.lower()).strip("_")


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not math.isnan(float(value))


if __name__ == "__main__":
    main()

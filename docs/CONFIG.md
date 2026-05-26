# Config

`config.yaml` is the runtime configuration for Reviewer. It intentionally keeps
only fields that the current code reads.

## Project

```yaml
project:
  output_dir: outputs
```

- `output_dir`: base directory for generated summaries, reviews, rendered VLM
  page images, and logs when paths are relative.

## Bench

```yaml
bench:
  root: ../DeepReview-Bench
  dev_split: ../DeepReview-Bench/splits/deepreview13k_test_dev.jsonl
  dev_output_dir: outputs/deepreview_bench/dev
```

- `root`: DeepReview-Bench root directory.
- `dev_split`: JSONL split used by `reviewer run-bench-dev`.
- `dev_output_dir`: output directory used by `reviewer run-bench-dev`.

The normal dev command reads these values from config:

```bash
python -m reviewer.cli run-bench-dev
```

`run-bench-dev` resumes by default by skipping IDs already present in
`results.jsonl`. Use `--fresh` to ignore existing results and process from the
selected start row again.

## Network

```yaml
network:
  all_proxy: ${ALL_PROXY}
  no_proxy: ${NO_PROXY}
  default_no_proxy:
    - localhost
    - 127.0.0.1
    - 0.0.0.0
```

- `all_proxy`: optional proxy used by OpenAI-compatible model clients.
- `no_proxy`: optional additional no-proxy values.
- `default_no_proxy`: default local addresses excluded from proxying.

## Models

Each model entry is passed to an OpenAI-compatible chat-completions client.

```yaml
models:
  summary:
    model: openai/gpt-5.5
    base_url: ${OPENAI_BASE_URL}
    api_key_env: OPENAI_API_KEY
    temperature: 0.2
    max_tokens: 4096
    top_p: 1.0
    timeout_seconds: 60
    max_retries: 3
```

Common fields:

- `model`: model name sent to the API.
- `base_url`: OpenAI-compatible API base URL. `/chat/completions` is appended
  automatically when needed.
- `api_key_env`: environment variable containing the API key. Use `api_key` only
  for explicit literal keys.
- `temperature`, `max_tokens`, `top_p`: generation parameters.
- `timeout_seconds`, `max_retries`: HTTP request behavior.

Configured model roles:

- `summary`: SummaryAgent.
- `agent`: Contribution, Soundness, and Presentation decision/review agents.
- `answer`: AnswerAgent tool-use loop.
- `final_review`: FinalReviewAgent.
- `vlm`: Presentation page-image inspection.
- `reranker`: chat-completion reranking of Semantic Scholar candidates.

For GPT-family names, `LLMClient` maps `max_tokens` to
`max_completion_tokens` and sends `temperature=1` for compatibility.

## Agents

```yaml
agents:
  contribution:
    model: agent
    answer_model: answer
    min_qa_turns: 3
    max_qa_turns: 10
    require_balanced_qa: true
```

- `model`: model role for dimension-agent decisions and final dimension review.
- `answer_model`: model role used by AnswerAgent for Q&A evidence gathering.
- `min_qa_turns`: minimum number of dimension-agent Q&A results required before
  the agent is allowed to write the dimension review.
- `max_qa_turns`: maximum number of dimension-agent Q&A turns before writing the
  dimension review.
- `require_balanced_qa`: if true, the agent must collect at least one Q&A result
  with `review_impact.polarity=strength` and at least one with
  `review_impact.polarity=weakness` before it can write the dimension review.

Presentation-specific fields:

- `vlm_model`: model role used by `VLMTool`.
- `use_vlm`: whether PresentationAgent attempts page-image inspection.
- `require_vlm`: if true, VLM failure aborts PresentationAgent. If false, the
  VLM error is recorded as an unavailable observation and review continues.
- `require_pdf`: if true, PresentationAgent requires PDF page text.

Final review:

- `agents.final.model`: model role for the final aggregate review.

Scoring rules are intentionally not configured here. ICLR rating scales live in
the prompts:

- `prompts/dimension_review_xml.md`: Contribution/Soundness/Presentation use
  1-4.
- `prompts/final_review_xml.md`: final recommendation uses 1, 3, 5, 6, 8, 10;
  confidence uses 1-5.
- `prompts/qa_answer_xml.md`: Q&A impact uses C1/C2/C3.

## Retrieval

```yaml
retrieval:
  enabled: true
  semantic_scholar:
    api_key_env: SEMANTIC_SCHOLAR_API_KEY
    endpoint: https://api.semanticscholar.org/graph/v1/paper/search
    timeout_seconds: 30
  search:
    limit_per_query: 20
    fields: [...]
  time_filter:
    enabled: true
  rerank:
    enabled: true
    model: reranker
    top_k: 8
    min_candidates: 15
```

- `enabled`: disables external scholarly retrieval when false.
- `semantic_scholar`: Semantic Scholar Graph API settings.
- `search.limit_per_query`: candidate count requested from Semantic Scholar.
- `search.fields`: Semantic Scholar fields requested.
- `time_filter.enabled`: drops papers after the reviewed paper submission date
  when the date is available.
- `rerank.enabled`: enables chat-completion reranking.
- `rerank.model`: model role used by the reranker.
- `rerank.top_k`: maximum reranked papers returned to AnswerAgent.
- `rerank.min_candidates`: minimum candidate count before reranking is attempted.

The search query itself is chosen by AnswerAgent and passed through verbatim.

## QA

```yaml
qa:
  max_answer_steps: 6
```

- `max_answer_steps`: maximum AnswerAgent tool-use steps before it is forced to
  write a final `<qa_result>`.

Allowed impact values are prompt-level contracts, not config-driven validators
in the current implementation.

## Paper

```yaml
paper:
  max_text_chars: 120000
  max_pdf_read_pages: 3
  presentation_pdf_pages: 3
  max_vlm_pages: 8
  page_image_dpi: 160
```

- `max_text_chars`: max paper text sent to SummaryAgent.
- `max_pdf_read_pages`: max pages one `read_pdf` tool call can read.
- `presentation_pdf_pages`: number of PDF pages preloaded for PresentationAgent.
- `max_vlm_pages`: number of PDF pages rendered for VLM inspection.
- `page_image_dpi`: PDF rendering DPI for VLM images.

## Logging

```yaml
logging:
  level: INFO
  log_file: outputs/logs/reviewer.log
```

- `level`: Python logging level.
- `log_file`: optional log path, relative to the repo root if not absolute.

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
  the agent is allowed to call `end_questions`.
- `max_qa_turns`: maximum number of dimension-agent Q&A turns before the runtime
  forces the final dimension-review writer.
- `require_balanced_qa`: if true, the agent must collect at least one Q&A result
  with `review_impact.polarity=strength` and at least one with
  `review_impact.polarity=weakness` before it can call `end_questions`.

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

- `prompts/contribution_review_writer_guidance.md`, `prompts/soundness_review_writer_guidance.md`,
  and `prompts/presentation_review_writer_guidance.md`: dimension-specific review-writer
  guidance.
- `prompts/dimension_review_output_contract.md`: shared dimension-review XML schema and
  1-4 score contract.
- `prompts/final_review_output_contract.md`: final recommendation uses 1, 3, 5, 6, 8, 10;
  confidence uses 1-5.
- AnswerAgent `end_answer` tool-call contract: Q&A impact uses C0-C4.

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
  max_format_retries: 3
```

- `max_answer_steps`: maximum AnswerAgent tool-use steps before it is forced to
  write a final `end_answer` tool call.
- `max_format_retries`: maximum AnswerAgent retries for malformed XML or
  invalid tool-call output. The AnswerAgent accepts exactly one `<tool_call>`
  per turn; `end_answer` is the terminating tool and carries the final answer
  fields.

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

---

# 模型调用机制（Model Client）

上面的字段参考说明了 `config.yaml` 写什么；这一部分说明 `LLMClient` / model factory **如何**解释这些字段。所有 Agent（Summary、Q&A、Dimension、Final Review）都通过这一层调用模型。

默认没有 `provider` 字段，约定是：**所有文本模型都按 OpenAI-compatible chat completion 格式调用**。如果显式写 `provider: claude_code`，则改走本机 Claude Code CLI（见下文）。`model` 字段原样传给 API：OpenRouter 写 `openai/gpt-5.5`，本地 vLLM 写 `local-review-model` + `base_url: http://localhost:8000/v1` + `api_key_env: null`。

## Endpoint 解析规则

`LLMClient` 根据 `base_url` 自动判断请求地址。如果 `base_url` 已包含 `chat/completions` 或 `messages`，则认为是完整 endpoint，直接使用；否则自动拼接 `/chat/completions`。

| `base_url` | 实际请求 |
| --- | --- |
| `https://openrouter.ai/api/v1` | `https://openrouter.ai/api/v1/chat/completions` |
| `http://localhost:8000/v1` | `http://localhost:8000/v1/chat/completions` |
| `http://localhost:8000/v1/chat/completions` | （原样，不再拼接） |

## API Key

推荐 `api_key_env`（运行时从环境变量读取，例如 `export OPENROUTER_API_KEY=...`）。本地服务不需要 key 时写 `api_key_env: null`。仅在需要字面量密钥时使用 `api_key`。

## 模型参数与 GPT 兼容转换

`LLMClient` 从 model config 读取这些参数：

```yaml
temperature: 0.2
max_tokens: 4096
top_p: 1.0
presence_penalty: 0.0
frequency_penalty: 0.0
stop: null
response_format: null
timeout_seconds: 60
max_retries: 3
```

配置统一使用 `max_tokens`。请求前 client 做兼容转换：

- 检测到 GPT 系列（如 `openai/gpt-5.5`、`gpt-4o`），把 `max_tokens` 自动转换成 `max_completion_tokens`，并把 `temperature` 设为 `1`。
- 发生转换时写 warning 日志（logger 名 `reviewer.models.llm_client`），需 `configure_logging(config)` 才会同时输出到日志文件。
- 非 GPT 模型继续按配置传 `max_tokens` 和 `temperature`。

调用 `generate` 时可覆盖参数：

```python
output = client.generate(messages, temperature=0.1, max_tokens=2048)
```

## 代理优先级

`network` 字段（见上文 Network 节）的生效优先级：

```text
model.no_proxy
  > network.no_proxy + network.default_no_proxy + environment NO_PROXY
```

某个 model 单独写了 `no_proxy` 时，使用该 model 的设置（典型用途：让本地 vLLM 请求跳过 `ALL_PROXY`）。

## Prompt Loading

prompt 文件放在 `prompts/`，代码通过 `utils/prompts.py` 读取，相对路径从 repo 根目录解析（Agent 不需关心当前工作目录）：

```python
from reviewer.utils.prompts import load_prompt, join_prompts

system_prompt = load_prompt("prompts/summary_agent_system.md", config=config)
combined = join_prompts(
    ["prompts/summary_agent_system.md", "prompts/summary_agent_output_contract.md"],
    config=config,
)
```

## Model Factory 与 Message 格式

通过 factory 构造 client，Agent 只需知道自己的 model key：

```python
from reviewer.models.factory import build_llm

client = build_llm(config, "summary")          # 对应 models.summary
output = client.generate(messages)             # 返回 assistant 文本，通常是 XML
```

`generate` 使用 OpenAI-style messages：

```python
messages = [
    {"role": "system", "content": "You are the Summary Agent."},
    {"role": "user", "content": "Paper text..."},
]
```

## 通过 Claude Code CLI 调用（provider: claude_code）

除了 OpenAI-compatible HTTP，模型还可走本机已登录的 `claude` CLI（headless `-p` 模式），动机通常是**用 Claude 订阅额度而非按 API token 计费**。实现于 `models/claude_code_client.py` 的 `ClaudeCodeClient`，对外暴露与 `LLMClient` 相同的 `generate(messages, **kwargs) -> str`，由 `factory` 按 `provider` 分流，**上层 Agent 无需改动**。

启用方式——用 profile 一次性切换：

```yaml
# config.yaml
model_profile: claude_code     # 或 models.active_profile / CLI --model-profile
```

`config.yaml` 内置该 profile（`models.profiles.claude_code` 下 `default.provider: claude_code`，各 model key 用 `opus`/`sonnet`/`haiku` 别名或全名）。也可只给单个 model key 设 `provider: claude_code` 混用两种后端。

实际执行的命令形如：

```bash
claude -p --output-format json --model <model> \
       --system-prompt "<system 消息>" \
       --max-turns 1 \
       --exclude-dynamic-system-prompt-sections \
       --tools ""
```

- **Claude 不调用任何自带工具**。本项目的「工具」（retrieval/python/vlm 等）由 Python 解析模型输出的 XML 后自行调用，从不走原生 tool-calling。关键是 `--tools ""`：把内置工具从模型视野移除，模型不会发起 tool_use。（`--allowed-tools ""` 只控制权限，模型仍看得见工具并尝试调用，会撞上 `--max-turns 1` 报 `error_max_turns`。）
- **采样参数被忽略**：`temperature`/`top_p`/`max_tokens` 在 CLI 无对应 flag；`base_url`/`api_key_env` 同样忽略（鉴权用 `claude` 登录态）。
- **system 消息**拼成 `--system-prompt`；其余轮次压平后从 stdin 传入。
- **图片（VLM）**：消息含 `image_url` block 时自动改用 `--input-format stream-json`，base64 传图，仍不启用任何工具。
- 可覆盖字段：`cli_command`（默认 `claude`）、`tools`（默认空=禁用全部）、`max_turns`（默认 1）、`extra_cli_args`、`timeout_seconds`、`max_retries`。
- 注意：一篇论文会产生几十次 CLI 调用，每次 spawn 进程并受订阅速率限制；跑 batch 时建议先调低 `bench.concurrency`。

## 当前边界

当前实现不支持 streaming（Reviewer 要解析完整 XML，一次性返回完整文本更易校验与修复）。

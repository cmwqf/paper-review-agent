<!--
用途：说明 Reviewer 第一层基础设施：config、prompt loading、OpenAI-compatible model client。
-->

# 配置、Prompt 与模型调用

本文档说明 Reviewer 当前已经实现的第一层基础设施：

- `config.yaml`
- prompt loading
- OpenAI-compatible `LLMClient`
- model factory
- 代理设置，包括 `ALL_PROXY` 和每个 model 的 `no_proxy`

这部分是所有 Agent 的共同依赖。Summary Agent、Q&A Tool、Dimension Agent 和 Final Review Agent 后续都会通过这层能力调用模型。

## 配置文件

Reviewer 当前只使用一个主配置文件：

```text
config.yaml
```

模型配置写在：

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

这里没有 `provider` 字段。当前约定是：**所有文本模型都按照 OpenAI-compatible chat completion 格式调用**。

`model` 字段会原样传给 API，因此 OpenRouter 可以写：

```yaml
model: openai/gpt-5.5
```

本地 vLLM 或其他 OpenAI-compatible 服务可以写：

```yaml
model: local-review-model
base_url: http://localhost:8000/v1
api_key_env: null
```

如果使用 OpenRouter，可以写：

```yaml
model: openai/gpt-5.5
base_url: https://openrouter.ai/api/v1
api_key_env: OPENROUTER_API_KEY
```

## Endpoint 解析规则

`LLMClient` 会根据 `base_url` 自动判断请求地址。

如果 `base_url` 已经包含：

```text
chat/completions
messages
```

则认为它已经是完整 endpoint，直接使用。

否则自动拼接：

```text
/chat/completions
```

例子：

```yaml
base_url: https://openrouter.ai/api/v1
```

实际请求：

```text
https://openrouter.ai/api/v1/chat/completions
```

例子：

```yaml
base_url: http://localhost:8000/v1
```

实际请求：

```text
http://localhost:8000/v1/chat/completions
```

例子：

```yaml
base_url: http://localhost:8000/v1/chat/completions
```

实际请求：

```text
http://localhost:8000/v1/chat/completions
```

## API Key

推荐使用 `api_key_env`：

```yaml
api_key_env: OPENROUTER_API_KEY
```

运行时会从环境变量读取：

```bash
export OPENROUTER_API_KEY=...
```

如果是本地服务，不需要 key，可以写：

```yaml
api_key_env: null
```

## 支持的模型参数

当前 `LLMClient` 会从 model config 中读取这些参数：

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

配置文件中统一使用 `max_tokens`。为了让配置保持简单，client 会在请求前做兼容转换：

- 如果检测到 GPT 系列模型，例如 `openai/gpt-5.5` 或 `gpt-4o`，则把 `max_tokens` 自动转换成 `max_completion_tokens`。
- 如果检测到 GPT 系列模型，则把 `temperature` 自动设置为 `1`。
- 发生上述自动转换时，client 会写 warning 日志。
- 非 GPT 模型继续传 `max_tokens` 和配置中的 `temperature`。

因此 GPT 模型仍然可以在 config 中这样写：

```yaml
models:
  summary:
    model: openai/gpt-5.5
    max_tokens: 4096
    temperature: 0.2
```

实际发送请求时会变成：

```json
{
  "model": "openai/gpt-5.5",
  "max_completion_tokens": 4096,
  "temperature": 1
}
```

这些 warning 使用 Python logging，logger 名称是：

```text
reviewer.models.llm_client
```

如果调用入口执行了：

```python
from reviewer.logging import configure_logging

configure_logging(config)
```

则 warning 会同时输出到 stderr 和 `config.yaml` 中的日志文件：

```yaml
logging:
  level: INFO
  log_file: outputs/logs/reviewer.log
```

调用 `generate` 时也可以覆盖参数：

```python
output = client.generate(
    messages,
    temperature=0.1,
    max_tokens=2048,
)
```

## 代理设置

全局代理设置在：

```yaml
network:
  all_proxy: ${ALL_PROXY}
  no_proxy: ${NO_PROXY}
  default_no_proxy:
    - localhost
    - 127.0.0.1
    - 0.0.0.0
```

`all_proxy` 用于外部服务，例如 OpenRouter。

`no_proxy` 用于跳过代理。默认建议包含本地地址，避免本地 vLLM 请求被代理转发。

每个 model 可以单独设置 `no_proxy`：

```yaml
models:
  local_answer:
    model: local-review-model
    base_url: http://localhost:8000/v1
    api_key_env: null
    no_proxy:
      - localhost
      - 127.0.0.1
      - 0.0.0.0
```

优先级是：

```text
model.no_proxy
  > network.no_proxy + network.default_no_proxy + environment NO_PROXY
```

如果某个 model 写了 `no_proxy`，则使用该 model 的设置。

## Prompt Loading

prompt 文件放在：

```text
prompts/
```

代码中通过 `utils/prompts.py` 读取：

```python
from reviewer.utils.prompts import load_prompt, join_prompts

system_prompt = load_prompt("prompts/summary_system.md", config=config)
format_prompt = load_prompt("prompts/summary_output_xml.md", config=config)

combined = join_prompts(
    ["prompts/summary_system.md", "prompts/summary_output_xml.md"],
    config=config,
)
```

相对路径会从 repo 根目录解析。因此 Agent 里不需要关心当前工作目录。

## Model Factory

推荐通过 factory 构造模型 client：

```python
from reviewer.models.factory import build_llm

client = build_llm(config, "summary")
output = client.generate(messages)
```

`summary` 对应：

```yaml
models:
  summary:
    ...
```

这样 Agent 只需要知道自己使用哪个 model key，不需要关心底层 HTTP 请求格式。

## Message 格式

`LLMClient.generate` 使用 OpenAI-style messages：

```python
messages = [
    {"role": "system", "content": "You are the Summary Agent."},
    {"role": "user", "content": "Paper text..."},
]
```

返回值是 assistant 的文本内容。对于 Reviewer，通常应该是 XML 字符串。

## 当前边界

当前第一版实现不支持 streaming。原因是 Reviewer 后续要解析完整 XML，一次性返回完整文本更容易校验和修复。

当前 `LLMClient` 主要面向文本模型。VLM client 仍是 scaffold，后续实现 Presentation Agent 时再补。

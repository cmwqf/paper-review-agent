# Reviewer

Reviewer 是一个用于论文评审的结构化 review-agent 项目。

整体流程是：

1. 生成 XML 格式的论文摘要和 paper map。
2. 分别运行三个维度 agent：Contribution、Soundness、Presentation。
3. 每个维度 agent 通过 Q&A 轨迹收集证据。
4. 每个 Q&A answer 都需要说明它对 review 的影响。
5. 汇总三个维度 review，生成最终综合 review。

## 快速开始

以下命令默认都在 `/root/autodl-tmp/review_agent/Reviewer` 下运行。

```bash
cd /root/autodl-tmp/review_agent/Reviewer
pip install -e .
cp .env.example .env
```

编辑 `.env`，填写 `config.yaml` 中使用的模型地址和 key：

```bash
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=http://your-openai-compatible-host/v1
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_key
NO_PROXY=localhost,127.0.0.1,::1,your-openai-compatible-host
```

模型服务需要兼容 OpenAI Chat Completions API。如果 `base_url` 是 `/v1`
根路径，Reviewer 会自动请求 `/chat/completions`。

### 运行单篇论文

```bash
PYTHONPATH=src python -m reviewer.cli run \
  --paper ../DeepReview-Bench/papers/0aR1s9YxoL/paper.pdf
```

输出会写到：

```text
outputs/reviews/<paper_id>/
```

### 运行 Benchmark Split

不加子命令时，CLI 默认按 `config.yaml` 中配置的 benchmark split 批量运行
Reviewer。具体跑哪个数据集由 `--split` 决定。

当前 `config.yaml` 中配置了这些 split：

```yaml
bench:
  root: ../DeepReview-Bench
  output_dir: outputs/deepreview_bench
  splits:
    dev: ../DeepReview-Bench/splits/deepreview13k_test_dev.jsonl
    lite: ../DeepReview-Bench/splits/deepreview13k_test_lite.jsonl
    test: ../DeepReview-Bench/splits/deepreview13k_test.jsonl
    all: ../DeepReview-Bench/splits/all.jsonl
  concurrency: 8
```

运行 dev：

```bash
PYTHONPATH=src python -m reviewer.cli --split dev
```

运行 lite：

```bash
PYTHONPATH=src python -m reviewer.cli --split lite
```

运行 all：

```bash
PYTHONPATH=src python -m reviewer.cli --split all
```

指定某个模型实验 agent，例如只把综合模型切到 `deepseek-v4-pro`：

```bash
PYTHONPATH=src python -m reviewer.cli --agent deepseek_v4_pro --split dev
```

常用参数：

```bash
# 小规模 smoke test，只跑 2 篇。
PYTHONPATH=src python -m reviewer.cli --split dev --limit 2

# 从 split 的某个 offset 开始跑。
PYTHONPATH=src python -m reviewer.cli --split lite --start 20 --limit 10

# 忽略 results.jsonl 的 resume 状态，重新跑所选范围。
PYTHONPATH=src python -m reviewer.cli --split dev --fresh

# 覆盖 config.yaml 中的 bench.concurrency。
PYTHONPATH=src python -m reviewer.cli --split dev --concurrency 4
```

输出目录规则：

```text
不传 --agent: outputs/deepreview_bench/<split>
传 --agent:   outputs/deepreview_bench/<split>_<agent>
```

例如：

```bash
PYTHONPATH=src python -m reviewer.cli --agent deepseek_v4_pro --split dev
# 输出到 outputs/deepreview_bench/dev_deepseek_v4_pro
```

### 评估输出

从仓库根目录 `/root/autodl-tmp/review_agent` 运行：

```bash
cd /root/autodl-tmp/review_agent
python get_metric.py Reviewer/outputs/deepreview_bench/dev_deepseek_v4_pro \
  --split-file DeepReview-Bench/splits/deepreview13k_test_dev.jsonl \
  --save-json Reviewer/outputs/deepreview_bench/dev_deepseek_v4_pro.metrics.json \
  --save-md Reviewer/outputs/deepreview_bench/dev_deepseek_v4_pro.metrics.md \
  --save-details Reviewer/outputs/deepreview_bench/dev_deepseek_v4_pro.metrics.details.jsonl
```

指标脚本会输出：

- Rating / Soundness / Presentation / Contribution 的 MSE 和 MAE
- 各维度 Spearman correlation
- Decision Accuracy 和 Decision F1
- Pairwise ranking accuracy

## 配置说明

`config.yaml` 是项目的主配置文件，负责模型路由、agent、检索、论文读取、
日志和输出路径。

### 模型默认配置和 Agent 配置

模型配置按以下顺序合并，后面的字段会覆盖前面的字段：

1. `models.default`
2. `models.<model_key>`
3. `models.profiles.<selected_agent>.default`
4. `models.profiles.<selected_agent>.<model_key>`

当前配置示例：

```yaml
models:
  default:
    model: openai/gpt-5.5
    base_url: ${OPENAI_BASE_URL}
    api_key_env: OPENAI_API_KEY
    temperature: 0.2
    max_tokens: 32768
    top_p: 1.0
    timeout_seconds: 60
    max_retries: 3

  profiles:
    deepseek_v4_pro:
      final_review:
        model: deepseek-v4-pro
```

当你运行：

```bash
PYTHONPATH=src python -m reviewer.cli --agent deepseek_v4_pro --split dev
```

只有 `final_review` 会使用 `deepseek-v4-pro`。没有设置的字段，例如
`base_url`、`api_key_env`、`max_tokens`、`timeout_seconds`，都会继承
`models.default`。

`--agent` 选择的是 `models.profiles` 下面的一个 key，用来切换一次运行的
模型实验配置。

```bash
PYTHONPATH=src python -m reviewer.cli --agent deepseek_v4_pro --split dev
```

仍然可以在 `models` 下写 `active_profile: deepseek_v4_pro` 作为默认启用的
agent，但更推荐运行时显式传 `--agent`，这样实验更清楚。命令行传入的
`--agent` 会覆盖 `active_profile`。

如果 DeepSeek 使用独立 endpoint 或 API key，可以在 agent profile 里单独写：

```yaml
models:
  default:
    model: openai/gpt-5.5
    base_url: ${OPENAI_BASE_URL}
    api_key_env: OPENAI_API_KEY
    temperature: 0.2
    max_tokens: 32768

  profiles:
    deepseek_v4_pro:
      final_review:
        model: deepseek-v4-pro
        base_url: ${DEEPSEEK_BASE_URL}
        api_key_env: DEEPSEEK_API_KEY
```

然后在 `.env` 中添加：

```bash
DEEPSEEK_BASE_URL=https://your-deepseek-compatible-host/v1
DEEPSEEK_API_KEY=your_deepseek_key
```

### 配置多个内部模型

每个工作流 agent 会引用一个模型 key：

```yaml
agents:
  summary:
    model: summary
  contribution:
    model: agent
    answer_model: answer
  soundness:
    model: agent
    answer_model: answer
  presentation:
    model: agent
    answer_model: answer
    vlm_model: vlm
  final:
    model: final_review
```

可以在一个 agent profile 中覆盖任意内部模型：

```yaml
models:
  profiles:
    deepseek_all:
      summary:
        model: deepseek-v4-pro
      agent:
        model: deepseek-v4-pro
        temperature: 0.3
      answer:
        model: deepseek-v4-pro
      final_review:
        model: deepseek-v4-pro
      reranker:
        model: deepseek-v4-pro
        max_tokens: 1024
```

如果某个 role 没有在选中的 agent profile 中配置，就会使用该 role 自己的
配置加上 `models.default`。

## 开发检查

```bash
PYTHONPATH=src pytest -q
```

只检查模型配置和 HTTP client：

```bash
PYTHONPATH=src pytest -q tests/test_settings.py tests/test_llm_client.py
```

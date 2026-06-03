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

每次新运行都会创建一个新的 GMT 时间戳目录，例如：

```text
outputs/deepreview_bench/runs/20260602_153012_GMT_dev_default/
```

单篇 paper 输出保存在：

```text
outputs/deepreview_bench/runs/<run_name>/papers/<paper_id>/
```

run 根目录还会保存：

```text
run_manifest.json
run_config.yaml
results.jsonl
errors.jsonl
logs/reviewer.log
```

每篇 paper 目录内会边生成边落盘，例如：

```text
summary.xml
summary.md
contribution.xml
soundness.xml
presentation.xml
qa_trajectory.json
qa_trajectory.md
final_review.xml
status.json
logs/trace.json
logs/trace.md
```

`status.json` 会记录这篇 paper 已完成到哪个阶段，以及整篇是否完成。

运行 lite：

```bash
PYTHONPATH=src python -m reviewer.cli --split lite
```

运行 all：

```bash
PYTHONPATH=src python -m reviewer.cli --split all
```

指定某个模型实验 agent，例如把三个维度总结和最终总结切到
`deepseek-v4-pro`：

```bash
PYTHONPATH=src python -m reviewer.cli --agent deepseek_v4_pro --split dev
```

常用参数：

```bash
# 小规模 smoke test，只跑 2 篇。
PYTHONPATH=src python -m reviewer.cli --split dev --limit 2

# 从 split 的某个 offset 开始跑。
PYTHONPATH=src python -m reviewer.cli --split lite --start 20 --limit 10

# 继续已有 run。会根据每篇 paper 目录里的 status.json 和落盘文件续跑。
PYTHONPATH=src python -m reviewer.cli \
  --resume outputs/deepreview_bench/runs/20260602_153012_GMT_dev_default

# 在已有 run 里重新跑所选范围。
PYTHONPATH=src python -m reviewer.cli \
  --resume outputs/deepreview_bench/runs/20260602_153012_GMT_dev_default \
  --fresh

# 覆盖 config.yaml 中的 bench.concurrency。
PYTHONPATH=src python -m reviewer.cli --split dev --concurrency 4
```

续跑规则：

- 已完整生成 `summary.xml`、三个维度 XML、`qa_trajectory.json` 中三个维度记录、`final_review.xml` 的 paper 会跳过。
- 如果某篇 paper 只完成了一部分，会从已有阶段继续补缺失阶段。
- 如果某个维度 XML 或该维度 Q&A 记录缺失，会重跑该维度。
- 如果补跑了任一维度，会重新生成 `final_review.xml`，避免最终评分基于旧维度结果。
- `--fresh` 会忽略这些已有落盘文件，对所选范围重新跑。

只复用已有 Q&A，重跑每个维度最后总结和最终总结：

```bash
PYTHONPATH=src python -m reviewer.cli \
  --agent deepseek_v4_pro \
  --split dev \
  --reuse-from outputs/deepreview_bench/runs/20260602_153012_GMT_dev_default \
  --fresh
```

这个模式会从 `--reuse-from` 指定的旧输出目录中读取：

```text
<old_run>/papers/<paper_id>/summary.xml
<old_run>/papers/<paper_id>/qa_trajectory.json
```

也兼容旧布局：

```text
<old_output>/<paper_id>/summary.xml
<old_output>/<paper_id>/qa_trajectory.json
```

然后只重新生成：

```text
<new_output>/<paper_id>/contribution.xml
<new_output>/<paper_id>/soundness.xml
<new_output>/<paper_id>/presentation.xml
<new_output>/<paper_id>/final_review.xml
```

它不会重新跑 summary agent，也不会重新跑每个维度的 Q&A 检索/回答过程。
这适合快速比较不同 `--agent` 在“维度总结”和“最终综合总结”上的影响。
如果模型输出的 XML 不合法，Reviewer 会把解析错误反馈给模型并重新生成，
直到 XML 合法或达到 `xml.max_generation_attempts` 上限。

输出目录命名规则：

```text
outputs/deepreview_bench/runs/YYYYMMDD_HHMMSS_GMT_<split>_<agent>/
```

例如默认模型：

```text
outputs/deepreview_bench/runs/20260602_153012_GMT_dev_default/
```

例如 deepseek profile：

```text
outputs/deepreview_bench/runs/20260602_153045_GMT_dev_deepseek_v4_pro/
```

### 评估输出

Benchmark 跑完后会自动评估当前 run，并把指标保存在当前 run 目录内：

```text
outputs/deepreview_bench/runs/<run_name>/metrics/
├── metrics.md
├── metrics.csv
├── metrics.json
├── details.jsonl
└── skipped.json
```

`get_metric.py` 在 Reviewer repo 内，也可以手动一次评估多个 run，并输出“每个
run 一行、每个指标一列”的对比表。建议把手动评估结果也保存在对应 run 的
`metrics/` 目录内。

方式一：直接在脚本顶部填写 `RUN_DIRS`：

```python
RUN_DIRS = [
    "outputs/deepreview_bench/runs/20260602_153012_GMT_dev_default",
    "outputs/deepreview_bench/runs/20260602_153045_GMT_dev_deepseek_v4_pro",
]
```

然后运行：

```bash
cd /root/autodl-tmp/review_agent/Reviewer
python get_metric.py \
  --save-md outputs/deepreview_bench/runs/20260602_153012_GMT_dev_default/metrics/metrics.md \
  --save-csv outputs/deepreview_bench/runs/20260602_153012_GMT_dev_default/metrics/metrics.csv \
  --save-json outputs/deepreview_bench/runs/20260602_153012_GMT_dev_default/metrics/metrics.json
```

方式二：命令行直接传多个 run：

```bash
cd /root/autodl-tmp/review_agent/Reviewer
python get_metric.py \
  outputs/deepreview_bench/runs/20260602_153012_GMT_dev_default \
  outputs/deepreview_bench/runs/20260602_153045_GMT_dev_deepseek_v4_pro \
  --save-md outputs/deepreview_bench/runs/20260602_153045_GMT_dev_deepseek_v4_pro/metrics/compare.metrics.md \
  --save-csv outputs/deepreview_bench/runs/20260602_153045_GMT_dev_deepseek_v4_pro/metrics/compare.metrics.csv
```

传 run 根目录或 `papers/` 子目录都可以。脚本会优先从
`run_manifest.json` 推断 split 文件；如果没有 manifest，再从 run 名推断。
也可以显式传 `--split-file ../DeepReview-Bench/splits/deepreview13k_test_dev.jsonl`。

指标脚本会输出：

- Rating / Soundness / Presentation / Contribution 的 MSE 和 MAE
- 各维度 Spearman correlation
- Decision Accuracy 和 Decision F1
- Pairwise ranking accuracy

## 配置说明

`config.yaml` 是项目的主配置文件，负责模型路由、agent、检索、论文读取、
日志和输出路径。

### 评审 Rubric Profile

当前 benchmark 按 ICLR 风格评测，因此默认配置为：

```yaml
review:
  rubric_profile: ICLR
```

运行时会把 `prompts/rubrics/iclr.md` 注入到 Contribution、Soundness、
Presentation、Answer Agent 和 Final Review 的 prompt 中。这个文件包含当前
会议的维度定义、1-4 维度分数说明、final score 说明和 confidence 说明。

如果之后要适配其他会议，新增一个文件，例如：

```text
prompts/rubrics/neurips.md
```

然后把配置改成：

```yaml
review:
  rubric_profile: NeurIPS
```

框架本身仍然使用通用的 Contribution / Soundness / Presentation agent；
具体会议要求通过 rubric profile 注入。

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
      agent:
        model: deepseek/deepseek-v4-pro
      final_review:
        model: deepseek/deepseek-v4-pro
```

当你运行：

```bash
PYTHONPATH=src python -m reviewer.cli --agent deepseek_v4_pro --split dev
```

`agent` 和 `final_review` 会使用 `deepseek/deepseek-v4-pro`。其中：

- `agent` 用于三个维度的最终总结：Contribution、Soundness、Presentation。
- `final_review` 用于最终综合总结。
- `answer` 没有在该 profile 中覆盖，因此仍然使用默认模型；在 `--reuse-from`
  模式下不会重新跑 Q&A，所以不会调用 `answer`。

没有设置的字段，例如 `base_url`、`api_key_env`、`max_tokens`、
`timeout_seconds`，都会继承 `models.default`。

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

### Presentation 的 PDF/VLM 设置

Presentation 现在默认不再把前几页 PDF 图片一次性喂给模型，而是允许
Answer Agent 在 Q&A 过程中主动调用 `inspect_visual`，指定一个目标
（例如 `Figure 2`、`Table 1` 或 `page 4`）。工具内部会决定给 VLM 哪张图：
图片内容优先使用 `figures/` 中提取好的 figure asset；表格格式、页面排版、
caption 拥挤等问题使用单页 PDF 渲染图。每次最多给 VLM 一张 PDF page。

相关配置：

```yaml
agents:
  presentation:
    use_vlm: true        # 允许使用 inspect_visual 视觉工具
    require_pdf: true    # 没有 PDF 证据时是否直接失败

paper:
  page_image_dpi: 220        # 渲染给 VLM 的页面图片 DPI
```

Presentation 不会在开头批量预加载 PDF 页面。视觉证据统一由 Answer Agent
在 Q&A 中按需调用 `inspect_visual` 获取。

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

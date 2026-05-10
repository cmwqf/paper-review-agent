<!--
用途：说明如何从 DeepReview-13K 或文本输入生成 paper_summary XML。
-->

# Summary Agent

Summary Agent 是 Reviewer 当前实现的第一个可运行 Agent。它负责把输入论文转换成结构化的 `<paper_summary>` XML，随后系统会把 XML 解析成 JSON-friendly 的 Paper Map，作为后续 Contribution、Soundness、Presentation 三个维度 Agent 的共同上下文。

Summary Agent 只负责记录论文信息，不负责评价论文。它不应该输出 weakness、review suggestion、missing baseline、missing information 等评审判断。评审相关内容由后续三个维度 Agent 完成。

后续 Reviewer 不应该只依赖 Summary。Summary 更像 Paper Map，用于帮助 Answer Agent 决定该搜索或读取论文的哪些部分；具体证据应通过 `search_file` 和 `read_file` 获取。

当前策略是：

```text
LLM output: XML
internal representation: JSON / Pydantic Paper Map
trace/output: XML + JSON
```

这样做的原因是：XML 对弱模型输出更稳，JSON 对程序处理和 trace 分析更方便。

## 支持的输入

当前支持：

- DeepReview-13K JSONL
- JSON object
- `.txt`
- `.md`
- `.tex`

DeepReview-13K 数据现在位于：

```text
/root/autodl-tmp/review_agent/DeepReview-13K
```

常用样本文件：

```text
/root/autodl-tmp/review_agent/DeepReview-13K/deepreview13k_test_lite/sample_2024.jsonl
```

## DeepReview-13K 字段映射

loader 会把一条 JSONL row 规范化成内部 paper dict。

主要字段映射：

```text
id              -> paper["id"]
title           -> paper["title"]
paper_context   -> paper["text"]
date            -> paper["metadata"]["submission_date"]
year            -> paper["metadata"]["year"]
decision        -> paper["metadata"]["decision"]
```

原始 row 会保存在：

```python
paper["raw"]
```

## 运行方式

可以通过 script 运行：

```bash
python scripts/run_summary.py \
  --config config.yaml \
  --input ../DeepReview-13K/deepreview13k_test_lite/sample_2024.jsonl \
  --index 0
```

也可以通过安装后的 CLI 运行：

```bash
reviewer --config config.yaml summarize \
  --input ../DeepReview-13K/deepreview13k_test_lite/sample_2024.jsonl \
  --index 0
```

如果不指定 `--output`，默认输出到：

```text
outputs/summaries/<paper_id>.xml
```

同时会保存解析后的 JSON：

```text
outputs/summaries/<paper_id>.json
```

## 模型调用

Summary Agent 使用：

```yaml
agents:
  summary:
    model: summary
```

也就是 `models.summary`。

prompt 来自：

```text
prompts/summary_system.md
prompts/summary_output_xml.md
```

## XML 校验

Summary Agent 会要求模型输出合法 XML，并校验 root tag 必须是：

```xml
<paper_summary>
```

如果模型输出被 markdown 包裹，例如：

```text
```xml
<paper_summary>...</paper_summary>
```
```

系统会尝试提取其中的 `<paper_summary>` XML 再校验。

当前只做 root tag 级别校验。完整字段级 schema 校验后续再补。

## Summary 与 Review 的边界

Summary XML 应该是 Paper Map + Global Index，而不是详细 review。它应该包含论文自己提供的信息，例如：

- section-level paper map
- section summaries
- key items per section
- claims
- method components
- datasets
- baselines
- ablations
- metrics
- results
- stated limitations

Summary XML 不应该包含：

- novelty 判断
- soundness 判断
- presentation 判断
- missing baseline 判断
- missing ablation 判断
- reviewer recommendation
- final score

如果某个字段没有在论文中出现，写 `unknown` 即可，不需要额外列出 `missing_information`。

## Paper Map XML 结构

模型输出 XML，格式大致如下：

```xml
<paper_summary>
  <metadata>
    <title>...</title>
    <authors>unknown</authors>
    <venue>unknown</venue>
    <submission_date>...</submission_date>
  </metadata>
  <paper_map>
    <section>
      <section_id>s1</section_id>
      <title>Introduction</title>
      <summary>...</summary>
      <key_items>
        <item>
          <type>problem</type>
          <text>...</text>
        </item>
      </key_items>
    </section>
  </paper_map>
  <global_index>
    <claims>
      <item section_ref="s1">...</item>
    </claims>
    <baselines>
      <item section_ref="s4">...</item>
    </baselines>
  </global_index>
</paper_summary>
```

内部会解析成 JSON-friendly schema，后续 Agent 可以直接使用 dict / Pydantic 对象。

## 环境变量

`load_config` 会自动读取 repo 根目录的 `.env` 文件。OpenRouter key 可以写在：

```text
.env
```

例如：

```text
OPENROUTER_API_KEY=...
```

不要把 `.env` 提交到 git。

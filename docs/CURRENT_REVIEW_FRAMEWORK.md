<!--
用途：记录当前 benchmark workflow 使用的 review 生成框架。
-->

# 当前 Review 框架

当前主流程是：

```text
paper
  -> summary XML / paper map
  -> 每个维度各自的 Q&A
  -> 每个维度各自的 dimension review
  -> final review
```

核心约束：**final review 不应该绕过 dimension review 直接重新基于 Q&A 写评审**。
Q&A 先在每个维度内部被聚合成该维度 review；final stage 再聚合三个维度
review，生成一个 ICLR 风格的最终 review 和推荐。

## 阶段边界

### Summary

Summary Agent 把论文事实抽取到 `summary.xml` 和 paper map。它不做评价，
不输出 novelty、soundness、presentation、recommendation 或 final score。

### Q&A

Contribution、Soundness、Presentation 三个维度各自收集自己的 Q&A
trajectory。每条 Q&A 会在 `qa_trajectory.json` 中保存稳定 id：

```text
CONTRIB-001
SOUND-001
PRES-001
```

三个维度只使用自己的 Q&A。例如 Soundness review writer 只看 Soundness
Q&A，不看 Contribution 或 Presentation Q&A。

### Dimension Review

写 dimension review 前，该维度的 Q&A 会被渲染成完整的 evidence ledger。
ledger 按 review impact 分组：

```text
C0 weaknesses
C1 weaknesses
C1 strengths
C2 weaknesses
C2 strengths
C3/C4 local or trace findings
```

每张 evidence card 包含：

- 稳定 Q&A id
- polarity、impact level、confidence
- review implication
- 完整 question
- 完整 answer
- paper / visual / evidence refs

`retrieved_papers` 不会进入 review writer 的输入。它们仍保留在
`qa_trajectory.json` 中用于 debug，但 dimension review 应该聚合 Q&A answer，
而不是重新基于检索结果做 related-work 判断。

dimension review writer 需要选择真正 decision-critical 的 Q&A findings，
给出 1-4 的维度分，并输出：

- `key_points`
- `strengths`
- `weaknesses`
- `evidence_summary`
- `rationale`
- `evidence_trace`

Contribution、Soundness、Presentation 使用各自的 review-writer prompt 来决定
哪些证据真正影响该维度判断；`dimension_review_output_contract.md` 只提供共享 XML schema
和通用 evidence-ledger/score-boundary 约束。

`evidence_trace` 记录 `supporting_qas`、`decisive_qas`、
`why_not_higher`、`why_not_lower` 和 score bounds。它是 final review 用来
审计该维度如何利用 Q&A 的接口。

### Final Review

Final Review Agent 的主输入是三个 dimension reviews。canonical Q&A evidence
bank 只作为 audit reference 提供，用于核对 Q&A id 和证据来源。final review
应该主要基于每个 dimension review 的 `key_points` 和 `evidence_trace` 聚合。

final review 保留 benchmark 需要的字段：

- `final_score`
- `recommendation`
- `confidence_score`

同时 final review 也会写 `evidence_trace`，方便后续 case study 追踪哪些 Q&A
id 和维度 findings 决定了最终分数。

## Artifact

每篇 paper 的 canonical artifacts 是：

```text
xml/summary.xml
xml/contribution.xml
xml/soundness.xml
xml/presentation.xml
xml/final_review.xml
markdown/summary.md
markdown/contribution.md
markdown/soundness.md
markdown/presentation.md
markdown/final_review.md
markdown/contribution_qa.md
markdown/soundness_qa.md
markdown/presentation_qa.md
markdown/qa_trajectory.md
qa_trajectory.json
status.json
logs/trace.json
logs/trace.md
```

以下文件不再写出：

```text
reused_qa_trajectory.json
markdown/reused_qa_trajectory.md
logs/reused_qa_trace.json
```

## 推荐的 Q&A 复用模式

固定当前 Q&A，只重新生成三个维度 review 和 final review：

```bash
PYTHONPATH=src python -m reviewer.cli \
  --split dev \
  --agent gpt-5.5 \
  --reuse-from outputs/deepreview_bench/runs/20260605_070951_GMT_dev_gpt-5_5 \
  --rerun-stages dimensions
```

这会创建一个新的 timestamp run，不会覆盖 source run。
输出目录名会把 profile 名 slug 化，例如 `gpt-5.5` 在目录名中会变成 `gpt_5_5`；命令行里推荐使用 `config.yaml` 的原始 profile 名。

如果使用 `--reuse-from` 但不传 `--rerun-stages`，默认等价于：

```text
--rerun-stages all
```

也就是重跑 Contribution、Soundness、Presentation 三个维度 review，并重跑
final review。它仍然不会重跑 summary 或 Q&A。

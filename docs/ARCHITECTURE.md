<!--
用途：记录 Reviewer repo 的整体架构思路，方便后续继续完善实现。
-->

# 架构设计

Reviewer 是一个面向论文评审的结构化多 Agent workflow。它的目标不是简单生成一段 review 文本，而是让评审过程具备清晰的模块边界、可追踪的证据链、可复现的中间结果，以及便于后续扩展的工程结构。

整体设计遵循一个原则：**Agent 专属逻辑放在 Agent 自己的目录中，共享能力放在公共模块中**。

- `agents/` 放 Summary、Contribution、Soundness、Presentation、Final Review 等 Agent 的专属逻辑。
- `tools/` 放 Agent 可调用的公共工具，例如 Q&A、retrieval、VLM、XML 校验。
- `workflow/` 负责整体流程编排。
- `schemas/` 定义模块之间传递的结构化数据。
- `models/` 封装 LLM、VLM、reranker 等模型调用。
- `retrieval/` 封装 Semantic Scholar 搜索、时间过滤、rerank 等检索逻辑。
- `paper/` 负责论文输入、文本抽取、PDF 页面渲染和 metadata 处理。

## 设计目标

1. **workflow 显式化**

   每个阶段都应该有明确的输入、输出和 trace。后续 debug 时，要能知道某个分数或某条 weakness 是从哪个 Q&A、哪条 evidence 推导出来的。

2. **Agent 模块化**

   Summary、Contribution、Soundness、Presentation、Final Review 分别放在不同文件夹中。这样每个 Agent 的 prompt、schema、控制逻辑可以独立演进。

3. **公共能力中心化**

   Q&A tool、retrieval、model client、XML validator、PDF loader、VLM tool 都是共享基础设施，不应该在每个 Agent 里重复实现。

4. **模型输出结构化**

   模型输出优先使用 XML。XML 先被校验和解析，再转成 Python schema，最后交给下游模块使用。

5. **保留证据和轨迹**

   每个维度 Agent 都是一个 Q&A trajectory。最终的维度 review 应该能从这个 trajectory 中解释出来。

## 端到端流程

单篇论文的预期流程是：

```text
paper input
  -> paper loader / text extractor / optional PDF page renderer
  -> Summary Agent
  -> paper_summary XML
  -> Contribution / Soundness / Presentation Agent Q&A trajectories in parallel
  -> three dimension_review XML documents
  -> Final Review Agent
  -> final_review XML
```

三个维度 Agent 都依赖 Summary Agent 的输出，但彼此不共享中间状态。因此在 Summary 生成之后，Contribution、Soundness、Presentation 会并行运行；Final Review Agent 等三个维度 review 全部完成后再运行。

Summary Agent 的职责边界需要保持清楚：它只记录论文自身信息，不做评价。它不应该输出 novelty 判断、soundness 判断、presentation 判断、missing baseline、missing ablation、review recommendation 或 final score。评价由后续三个维度 Agent 完成。

Summary 当前采用 “LLM 输出 XML，内部转 JSON” 的策略。模型输出 `<paper_summary>` XML，系统随后解析成 JSON-friendly 的 Paper Map schema。这样 XML 负责提高弱模型输出稳定性，JSON/Pydantic 负责后续程序处理和 trace 保存。

## 评审维度

Reviewer 对齐三个 ICLR 风格的评审维度。

### Contribution

Contribution 关注：

- 论文是否有足够 novelty
- 与已有工作的区别是否清楚
- 贡献是否实质性
- 潜在影响力是否足够
- 是否只是已有方法的轻微组合或工程改动

### Soundness

Soundness 关注：

- 技术方案是否可靠
- 假设是否合理
- 实验设计是否支持论文 claims
- baseline 是否充分
- ablation 是否充分
- 统计分析和指标是否合理
- 是否存在明显方法漏洞或实验漏洞

### Presentation

Presentation 关注：

- 论文表达是否清楚
- 结构是否合理
- 图表是否清晰
- caption 和符号说明是否充分
- 格式是否规范
- 是否存在排版、可读性、视觉呈现问题

Presentation 是唯一默认需要 VLM 的维度。VLM 主要用于观察 PDF 页面、图表、表格和排版，不应该承担主要技术正确性判断。

## Repo 结构

当前 repo 结构是：

```text
Reviewer/
├── config.yaml
├── prompts/
├── docs/
├── scripts/
├── examples/
├── outputs/
├── tests/
└── src/reviewer/
    ├── agents/
    ├── workflow/
    ├── tools/
    ├── retrieval/
    ├── models/
    ├── paper/
    ├── schemas/
    └── utils/
```

## 配置文件设计

当前阶段只使用一个主配置文件：

```text
config.yaml
```

这个文件负责定义：

- project 名称和输出目录
- 各类模型配置
- 每个 Agent 的设置
- retrieval 设置
- Q&A impact 约束
- paper 解析和 VLM 页面渲染设置
- XML 校验和修复设置
- logging 设置

模型定义放在：

```yaml
models:
  summary: ...
  agent: ...
  answer: ...
  final_review: ...
  vlm: ...
  reranker: ...
```

Agent 配置通过 key 引用模型配置，例如：

```yaml
agents:
  contribution:
    model: agent
    answer_model: answer
```

这表示 Contribution Agent 的决策模型使用 `models.agent`，Q&A answer 使用 `models.answer`。这样既保持单配置文件，又避免每个 Agent 重复写完整模型参数。

## Agent 目录设计

`agents/` 下每个主要 Agent 都有独立目录：

```text
agents/
├── summary/
├── answer/
├── contribution/
├── soundness/
├── presentation/
└── final/
```

每个 Agent 目录一般包含：

- `agent.py`

  该 Agent 的控制逻辑。

- `prompts.py`

  该 Agent 使用的 prompt 路径或 prompt 加载逻辑。

- `schema.py`

  该 Agent 专属的 schema alias 或扩展。

公共 Agent 逻辑放在：

- `agents/base.py`

  所有 Agent 共享的基础类和上下文对象。

- `agents/dimension_base.py`

  Contribution、Soundness、Presentation 共享的 Q&A trajectory 状态机。

这样做的原因是：三个维度 Agent 的高层流程类似，但评审目标和 prompt 不同。

### Answer Agent

Answer Agent 是 Q&A 流程中的证据获取和回答模块。它不是一个简单的 Answer model，而是一个可以自行决定是否读取论文、是否做外部检索的小型 Agent。

职责边界：

- Dimension Agent 决定要问什么 review question。
- Answer Agent 决定为了回答这个问题，需要哪些 evidence。
- Answer Agent 可以调用 `search_file`、`read_file` 和外部 `retrieval`。
- Answer Agent 最终输出结构化 `<qa_result>`，其中包含 answer、evidence summary、trace refs 和 review impact。

预期 action loop：

```text
question + dimension + paper_map + compact context
  -> choose action
     -> search_file
     -> read_file
     -> search_scholar
     -> write_answer
  -> when write_answer:
       output QAResult
```

Answer Agent 不应该只凭 Summary 回答需要证据的问题。Summary 是导航图，不是唯一事实来源。

## Workflow 模块

`workflow/` 只负责整体编排，不应该关心底层模型如何调用。

- `workflow/state.py`

  定义单篇论文 review 过程中的状态，包括 paper、summary、三个维度 review、trace 和 final review。

- `workflow/review_workflow.py`

  执行完整流程：Summary -> 三个维度 Agent -> Final Review。

- `workflow/trace.py`

  保存每个 Agent 的 Q&A trajectory、action、answer 和中间结果。

## Tools 模块

`tools/` 是 Agent 可以调用的公共工具层。

### QATool

文件位置：

```text
tools/qa_tool.py
```

职责：

- 接收一个维度相关的 review question
- 接收当前 dimension
- 接收是否需要 retrieval
- 如果需要 retrieval，调用 RetrievalTool
- 调用 Answer model 回答问题
- 返回结构化 `QAResult`

QATool 的输出不仅要有 answer，还必须包含这个 answer 对当前维度 review 的影响。

后续实现中，`QATool` 可以作为薄 wrapper：Dimension Agent 调用 `QATool.ask(...)`，而 `QATool` 内部调用 Answer Agent 完成证据获取和回答。这样可以保留外层“Q&A tool”接口，同时让 answer 过程具备 Agent 行为。

### RetrievalTool

文件位置：

```text
tools/retrieval_tool.py
```

职责：

- 调用 query generator 生成 search tags / queries
- 调用 Semantic Scholar 搜索相关论文
- 根据投稿时间做 time filter
- 对候选论文 rerank
- 返回 top retrieved papers

### PaperSearchTool

文件位置：

```text
tools/paper_search_tool.py
```

职责：

- 在 reviewed paper 内搜索相关 section 或 chunk
- 输入 query，例如 `baselines and ablations`
- 返回紧凑结果：`chunk_id`、`section_id`、score、短 snippet
- 默认不返回长原文，避免污染后续 Agent prompt
- 第一版可以用关键词搜索，后续升级成 embedding retrieval

### PaperReadTool

文件位置：

```text
tools/paper_read_tool.py
```

职责：

- 根据 `chunk_id`、`section_id` 或 char range 读取原文
- 返回当前 Answer Agent step 需要的 raw text
- raw text 应保存进 full trace
- raw text 不应默认拼进后续 Agent 的长期上下文

### VLMTool

文件位置：

```text
tools/vlm_tool.py
```

职责：

- 接收 PDF 页面截图或图表图片
- 回答 Presentation 相关视觉问题
- 输出可被 Presentation Agent 使用的观察结果

### XML Validator

文件位置：

```text
tools/xml_validator.py
```

职责：

- 校验模型输出是否是合法 XML
- 校验 root tag 是否正确
- 后续支持 XML repair
- 保留原始输出和修复后输出，方便 debug

## Retrieval 模块

`retrieval/` 负责 scholarly search 的内部细节。

- `query_generator.py`

  将 review question 转成 search tags 和 expanded queries。

- `semantic_scholar.py`

  Semantic Scholar Graph API client。

- `time_filter.py`

  根据 reviewed paper 的 submission date 过滤未来论文，避免信息泄露。

- `reranker.py`

  对 retrieved papers 按相关性重排。

- `types.py`

  定义 normalized retrieved paper 数据结构。

## Model 模块

`models/` 负责隐藏不同模型服务的调用细节。

- `llm_client.py`

  普通文本模型调用，用于 Summary、Agent decision、Q&A answer 和 Final Review。

- `vlm_client.py`

  VLM 调用，用于 Presentation 维度。

- `reranker_client.py`

  本地或远程 reranker 服务调用。

- `factory.py`

  根据 `config.yaml` 构造不同模型 client。

后续如果切换 OpenAI-compatible endpoint、本地 vLLM、OpenRouter 或其他服务，原则上只需要改 `models/` 和 `config.yaml`。

## Paper 模块

`paper/` 负责将原始论文输入转成 workflow 可用的数据。

- `loader.py`

  加载 PDF、txt 或结构化输入。

- `text_extractor.py`

  抽取论文正文文本，供 Summary Agent 和其他 LLM 模块使用。

- `pdf_pages.py`

  将 PDF 页面渲染成图片，供 VLMTool 使用。

- `metadata.py`

  标准化标题、venue、submission date 等 metadata。

## Schemas 模块

`schemas/` 定义模块之间传递的结构化数据。

- `summary.py`

  `<paper_summary>` 对应的数据结构。

- `qa.py`

  `QAResult` 和 `ReviewImpact`。

- `review.py`

  单个维度的 review。

- `final_review.py`

  最终综合 review。

- `xml.py`

  XML parse / serialize / helper 函数。

## Dimension Agent 的 Q&A Trajectory

Contribution、Soundness、Presentation 都应该共享同一种状态机：

```text
observe paper_summary + previous QA results
  -> decide action
     -> ask_question
     -> write_review
  -> if ask_question:
       call QATool(question, dimension, need_retrieval)
       append QAResult to trace
       continue
  -> if write_review:
       generate dimension_review XML
       stop
```

Agent 的 action 也建议用 XML 表示，例如：

```xml
<agent_action>
  <action>ask_question</action>
  <question>Are the baselines sufficient for this task?</question>
  <need_retrieval>true</need_retrieval>
  <rationale>The summary lists baselines but does not establish whether they are current.</rationale>
</agent_action>
```

当 Agent 认为证据已经足够时，输出：

```xml
<agent_action>
  <action>write_review</action>
  <rationale>The trajectory has enough evidence to score this dimension.</rationale>
</agent_action>
```

每个 Agent 必须受 `config.yaml` 中 `max_qa_turns` 控制，避免无限循环。

## Q&A Result 设计

Q&A answer 是这个系统的关键结构。它不应该只是回答问题，还应该明确说明这个回答如何影响当前维度的 review。

预期 XML 结构：

```xml
<qa_result>
  <question>Are the baselines sufficient?</question>
  <answer>...</answer>
  <evidence>
    <item source="paper">...</item>
    <item source="retrieval">...</item>
    <item source="inference">...</item>
  </evidence>
  <retrieved_papers>
    <paper>
      <title>...</title>
      <year>...</year>
      <url>...</url>
      <relevance>...</relevance>
    </paper>
  </retrieved_papers>
  <review_impact>
    <dimension>Soundness</dimension>
    <polarity>weakness</polarity>
    <severity>major</severity>
    <score_impact>-1.5</score_impact>
    <confidence>high</confidence>
    <rationale>...</rationale>
  </review_impact>
</qa_result>
```

`review_impact.polarity` 的候选值：

- `strength`
- `weakness`
- `neutral`
- `mixed`

`review_impact.severity` 的候选值：

- `minor`
- `moderate`
- `major`
- `critical`

`score_impact` 是局部信号，不等于最终维度分数。维度 Agent 在 `write_review` 时应该综合整个 trajectory，而不是简单累加所有 `score_impact`。

## Summary、Search File 与 Read File 的关系

后续系统不应该只靠 Summary，也不应该每一步都塞整篇论文。

推荐关系是：

```text
Summary / PaperMap = 高层目录和全局索引
search_file = 在论文中找相关位置
read_file = 读取具体证据
retrieval = 查外部相关论文
```

Summary 用于帮助 Agent 判断该问什么、该从哪里开始查；真正影响 review 的 answer 应该尽量有 `read_file` 或 `retrieval` 证据支持。

后续拼 Agent trace 时，需要区分：

- Full Trace：完整保存 raw paper chunks 和 retrieval results，用于 debug 和复现。
- Agent Memory：只保留 question、answer、evidence summary、review impact 和 refs。
- Tool Scratchpad：当前工具调用临时使用的 raw evidence，不默认进入下一轮 prompt。

## Retrieval 流程

当某个 Q&A question 需要 retrieval 时，流程是：

```text
question + dimension + paper metadata
  -> query generator
  -> search tags / expanded queries
  -> Semantic Scholar search
  -> normalize papers
  -> time filter
  -> reranker
  -> top retrieved papers
  -> answer model
  -> QAResult
```

retrieval 需要明确区分证据来源：

- 来自当前论文的证据：`source="paper"`
- 来自检索论文的证据：`source="retrieval"`
- 模型基于证据做出的推断：`source="inference"`

这个区分很重要。Final Review 不应该把模型推断误当成论文事实，也不应该把检索结果中没有支持的内容写成确定结论。

## Time Filter

Time filter 的作用是避免未来信息泄露。

如果 reviewed paper 有 submission date，那么检索到的论文中，publication date 晚于 submission date 的论文不应该影响 review。

默认策略：

```text
如果 retrieved paper 没有 publication_date，则保留
如果 publication_date <= submission_date，则保留
如果 publication_date > submission_date，则过滤掉
```

没有日期的论文暂时保留，因为 Semantic Scholar 记录可能不完整。Answer model 在引用这类论文时应该保持谨慎。

## VLM 使用边界

VLM 主要给 Presentation Agent 使用。

它可以判断：

- 页面布局是否混乱
- 图表是否清晰
- 表格是否可读
- caption 是否充分
- 字体、排版、对齐是否存在明显问题
- 公式或符号展示是否影响阅读

它不应该主要判断：

- 方法是否 mathematically sound
- baseline 是否充分
- 实验结论是否成立
- novelty 是否足够

如果视觉问题影响技术判断，例如图里的曲线不可读、坐标轴缺失、表格指标不清楚，Presentation Agent 可以把这个问题记录为 presentation weakness，Final Review Agent 可以在最终 review 中综合体现。

## XML 与 Schema 策略

模型输出采用 XML，原因是 review workflow 需要明确字段、明确层次，并且方便保存 trace。

推荐处理链路：

```text
model XML output
  -> XML validation
  -> typed schema object
  -> downstream module
```

后续实现需要补齐：

- root tag 校验
- required fields 校验
- polarity / severity 枚举校验
- score 范围校验
- XML repair
- 原始 XML 和修复后 XML 的 trace 保存

## Trace 与输出

每次运行建议保存三类产物：

```text
outputs/traces/<paper_id>.json
outputs/reviews/<paper_id>.xml
outputs/logs/reviewer.log
```

`traces` 应该包含：

- paper metadata
- Summary Agent 输出
- 每个 dimension Agent 的 action
- 每次 Q&A 的 question
- retrieval queries
- retrieved papers
- rerank 结果
- Q&A answer
- review impact
- dimension review
- final review

trace 是 debug 的核心。如果某个 final score 不合理，应该能沿着 trace 找到是哪一个 Agent、哪一个 Q&A、哪一条 evidence 导致的。

## 建议实现顺序

建议按以下顺序逐步实现：

1. 实现 config 读取和环境变量展开。
2. 实现 prompt loading。
3. 实现 OpenAI-compatible `LLMClient`。
4. 实现文本论文加载和 PDF 文本抽取。
5. 实现 Summary Agent 的 XML 生成和解析。
6. 实现不带 retrieval 的 QATool。
7. 实现共享 DimensionAgent loop。
8. 实现 Contribution 和 Soundness Agent。
9. 实现 Semantic Scholar retrieval。
10. 实现 query generation、time filter、reranker。
11. 实现不带 VLM 的 Presentation Agent。
12. 实现 PDF 页面渲染和 VLMTool。
13. 实现 Final Review Agent。
14. 实现 trace 保存。
15. 实现 batch review 和评测脚本。

这个顺序的好处是：先把核心闭环跑通，再逐步加入 retrieval 和 VLM 的复杂度。

## 当前未定设计问题

以下问题暂时不需要立刻定死，可以在第一版 end-to-end prototype 跑起来后再决定：

- 每个维度是否需要不同的 agent model？
- retrieved papers 是直接传给 Answer model，还是先做摘要压缩？
- Final Review Agent 应该看到完整 Q&A trace，还是只看三个维度 review 和高影响 evidence？
- Presentation 分数在 final score 中的权重是否应该低于 Contribution 和 Soundness？
- `score_impact` 是否只作为解释性信号，还是参与分数聚合？

这些问题会影响最终系统行为，但不影响当前 repo 的工程骨架。

# Q&A Trajectory

## Contribution

### Q1

**Question:** How novel are DACCA's main components—positive sample memory modules with domain-level lane features, cross-domain contrastive loss, and domain-level feature aggregation—relative to prior UDA/contrastive/prototype/context-aggregation methods cited in the paper?

**Answer:** DACCA appears to be mainly an adaptation and combination of existing UDA contrastive/prototype-memory and context-aggregation ideas for segmentation-based lane detection, rather than a major new conceptual advance. Its more specific contribution is to tailor these ideas to lane detection by storing per-lane, per-domain “domain-level lane features” in positive sample memory modules, using them as positives in source/target contrastive losses, and reusing the same source/target domain-level features for feature aggregation. This is a meaningful application-level contribution because the paper targets a narrow UDA lane-detection setting and reports improvements over adapted contrastive and context modules. However, the core ingredients—class/domain prototypes or memory, contrastive alignment across domains, teacher-student pseudo-labeling, and feature/context aggregation—are all close to prior UDA semantic-segmentation methods cited by the paper, including CDCL, ProCA, CONFETI, SePiCo, Cross-domain/SAM-style aggregation, and MLDA-like domain-adaptive lane detection. The novelty is therefore incremental: the paper packages and specializes these mechanisms for lane classes and lane-domain context, but it does not establish a fundamentally new UDA principle.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper itself positions DACCA around two claimed components: cross-domain contrastive learning and domain-level feature aggregation. According to the paper map, it argues that previous pseudo-label-based positive sampling can assign false positive samples in the unlabeled target domain, and DACCA instead uses positive sample memory modules to store source and target domain-level lane features as positives.
- paper: The method description indicates that PSMMs store per-lane domain-level features separately for source and target domains, are initialized from selected anchor feature centers, and are updated by EMA. This closely resembles prototype/memory-bank mechanisms already common in contrastive and prototype-based UDA methods, with the lane/domain specialization being the main adaptation.
- paper: The cross-domain contrastive loss is category-wise: anchors are selected from confident lane pixels, positives come from the source/target PSMMs, and negatives are selected from low-confidence pixels. The paper compares this component experimentally against CDCL, ProCA, CONFETI, and SePiCo, which suggests the authors view the contribution as a variant or replacement of existing contrastive/prototype losses rather than an entirely new family of methods.
- paper: The domain-level feature aggregation module assigns source and target PSMM features to pixel locations, concatenates those assigned domain-level maps with pixel-level features, and fuses them by a 1x1 convolution. The paper also compares this to Cross-domain and self-attention module aggregation baselines, implying that the aggregation idea is related to existing context-aggregation mechanisms, with DACCA’s specific distinction being use of stored source/target lane-domain features.
- paper: The paper's empirical ablations show that adding SCCL, self-training/TCCL, DFA, and unreliable-background-pixel aggregation improves performance, and it reports better results than several UDA lane-detection and adapted UDA segmentation baselines. This supports that the combination is practically useful in its domain even if the conceptual building blocks are borrowed.
- retrieval: No external scholarly retrieval results were available in the provided tool observations, so the novelty judgment is based on the paper’s own related-work positioning, method descriptions, and comparisons to cited methods.
- inference: Because memory/prototype contrastive learning, cross-domain feature alignment, pseudo-label self-training, and context aggregation are all established ideas in the cited UDA literature, DACCA’s contribution is best characterized as an effective domain-specific synthesis for lane detection, not a substantive conceptual breakthrough.

## Soundness

### Q1

**Question:** Do the experiments report variance or multiple random seeds, and are the main comparisons to UDA baselines conducted under comparable settings such as the same backbone, training data, input resolution, and evaluation protocol?

**Answer:** The experiments appear to report only single-point results, with no reported variance, confidence intervals, or multiple-random-seed averages. This weakens the statistical support for the claimed gains, especially because some improvements over UDA baselines are modest. The paper does provide some common experimental-setting details—e.g., dataset/task definitions, metrics, input image size of 384x800, optimizer settings, and use of standard TuLane/CULane/Tusimple-style metrics—and it includes comparisons using named backbones such as SCNN, ERFNet, and RTFormer. However, the main UDA baseline comparisons are not fully demonstrated to be controlled under identical settings. In particular, the paper compares against a mixture of domain-adaptive lane-detection and domain-adaptive segmentation methods, some apparently adapted or reported from prior work, and it is not clear from the available experimental description that every baseline uses exactly the same backbone, training data split, input resolution, training schedule, and evaluation implementation. Thus, the comparisons are directionally useful but not maximally sound as controlled head-to-head experiments.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper summary indicates that Appendix A.1 provides implementation details including AdamW, initial learning rate 0.0001, Poly learning-rate policy, image size 384x800, one Tesla V100 GPU, and dataset-specific metrics: Accuracy/FP/FN for TuLane, MuLane, MoLane, and Tusimple, and F1 for CULane/OpenLane.
- paper: The main results include Table 2 varying DACCA across SCNN, ERFNet, and RTFormer, and Table 3 comparing against UDA baselines including DANN, ADDA, SGADA, SGPCS, LD-BN-ADAPT, MLDA, PyCDA, Cross-domain, and Maximum Squares.
- paper: The provided paper map does not identify any reporting of standard deviation, confidence intervals, repeated runs, or multiple random seeds in the experimental sections or appendix.
- inference: Because no variance or seed information is reported, it is difficult to judge whether improvements such as DACCA over MLDA/PyCDA-type baselines are robust to training stochasticity.
- inference: Although shared metrics and some implementation settings are described, the evidence is insufficient to conclude that all UDA baselines were retrained under the same backbone, input resolution, training data, and schedule; therefore the baseline comparison is only partially controlled.

### Q2

**Question:** Do the ablations include a strong self-training-only baseline and variants that isolate each proposed component (SCCL, TCCL, DFA, UBP, PSMM/memory design) under the same backbone, and do the results show that each component consistently improves performance rather than relying mainly on the self-training pipeline?

**Answer:** No, not fully. The paper includes a useful component ablation under a single SCNN backbone, with rows that add SCCL, self-training, TCCL, DFA, and UBP feature aggregation, and the reported full DACCA result improves TuLane accuracy from the SCNN source-only baseline of 77.42% to 83.99%. This gives some evidence that the proposed pipeline helps. However, the ablation is primarily cumulative rather than a complete isolation of each component. It does not appear to provide a strong self-training-only baseline across the stronger backbones used in the main results, such as ERFNet or RTFormer, nor does it isolate PSMM/memory design choices separately from SCCL/TCCL/DFA. Because the main component study is on SCNN and the generalization table compares only source-only versus full DACCA for SCNN, ERFNet, and RTFormer, the evidence is insufficient to show that each proposed component consistently improves performance under the same backbone and across model capacity/dataset settings. The ablations support that the full method works, but they leave open whether gains are driven mainly by the self-training pipeline plus cumulative additions rather than by each individual proposed mechanism.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper’s component ablation, described as Table 1, uses an SCNN source-only baseline and adds SCCL, self-training, TCCL, DFA, and UBP feature aggregation; the reported source-only SCNN accuracy on TuLane is 77.42%, while full DACCA reaches 83.99%.
- paper: The paper’s generalizability experiment, described as Table 2, evaluates full DACCA with SCNN, ERFNet, and RTFormer, but this comparison is source-only versus full DACCA rather than self-training-only and per-component variants for each backbone.
- paper: The method’s SCCL, TCCL, and DFA all rely on positive sample memory modules/domain-level features, while the reported ablations do not separately test alternative memory designs, removal of PSMM, or PSMM update/initialization variants as independent causal factors.
- inference: A cumulative SCNN-only ablation can show that the final recipe improves over source-only, but it is weaker evidence for Soundness than a factorial or matched-backbone ablation including: source-only, self-training-only, SCCL-only, TCCL-only, DFA-only, UBP-only, no-PSMM/alternative-memory, and full DACCA across the same backbone(s).

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall legibility**
  - Main body text is readable and generally follows an ICLR-like single-column layout.
  - A major visual issue throughout pages **1–8** is extensive **red and blue inline text** in the title, abstract, body, tables, and method descriptions. This looks like revision markup or highlighting and is distracting/unusual for a clean ICLR submission.

- **Figures**
  - **Page 2, Figure 1:** Diagram is conceptually clear, but many internal labels and symbols are very small; readability is poor without zooming. Caption is informative and connected to the two subfigures.
  - **Page 3, Figure 2:** Framework diagram is dense and visually compressed. Subfigure labels and module text are hard to read, especially in the upper training-pipeline diagram. Caption is helpful but long.
  - **Page 6, Figure 3:** Image is legible and green lane/background markings are visible, but the figure is relatively small. Caption is concise but somewhat minimal; it does not fully explain why these pixels are “unreliable.”
  - **Page 8, Figure 4:** Bar charts are readable at a high level, with value labels visible, but axis/legend text is small. Caption clearly describes the comparisons.
  - **Page 8, Figure 5:** Qualitative image grid is visually useful, but individual images and lane markings are quite small; details are difficult to inspect. Caption is informative and maps rows to datasets.

- **Tables**
  - **Page 7, Table 1:** Mostly legible, but compact. Checkmark columns and red-highlighted values are understandable. Caption is very brief but adequate.
  - **Page 7, Table 2:** Legible and well aligned; bold values help identify best results. Caption explains the source-only symbol.
  - **Page 8, Table 3:** Dense and somewhat small due to fitting many rows on the page. Still readable with zoom, but could benefit from slightly larger font or more spacing. Caption is clear but minimal.

- **Captions**
  - Captions generally connect to the visual content and explain subfigures/tables.
  - Some captions are either **too terse** for standalone interpretation, e.g., Figure 3, or **quite long**, e.g., Figure 2. Overall acceptable but could be balanced.

- **Layout and formatting**
  - **Page 1:** Title is very large, bright red, small-caps, and hyphenated across lines; this looks nonstandard and harms professional presentation. Abstract also contains colored text.
  - **Pages 1–8:** Frequent red/blue text creates the strongest formatting concern. If intentional emphasis, it should be removed or greatly reduced for final submission.
  - **Pages 2–3:** Figures are placed well near relevant discussion, but diagrams are scaled down too much.
  - **Page 8:** Page is visually crowded with two figures, one large table, and the start of a subsection; inspection is possible but cramped.

- **Equations**
  - **Pages 4–6:** Equations are generally well formatted, numbered consistently, and mostly readable.
  - Some long set definitions and multi-line equations, especially on **pages 5–6**, are dense but not visibly broken or overflowing.

- **Ease of visual inspection as an ICLR submission**
  - Structurally, yes: header, page numbers, sections, figures, tables, and equations are recognizable and mostly organized.
  - Presentation would be significantly improved by removing colored inline markup, enlarging dense diagrams/qualitative figures, and reducing crowding on figure/table-heavy pages.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

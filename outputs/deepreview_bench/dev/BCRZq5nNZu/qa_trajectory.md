# Q&A Trajectory

## Contribution

### Q1

**Question:** How novel are the paper's two main claimed contributions—(1) defining/analyzing “chunking” as continual learning without task shift, and (2) per-chunk weight averaging—relative to prior work in online/i.i.d. streaming learning, catastrophic forgetting without task shift, and weight averaging methods such as Polyak/SWA/EMA/model soups? Are these framed as substantially new ideas or mostly a repackaging/application of known concepts?

**Answer:** The novelty appears moderate-to-limited. The paper’s strongest contribution is not that “chunking” is a fundamentally new learning setting, but that it reframes an i.i.d./same-task streaming or batched-online learning problem as an important subproblem inside continual learning, then empirically quantifies how much of the offline-to-continual-learning gap remains even when task shift is removed. That framing and empirical isolation are useful, but the underlying setting—sequential access to data from the same distribution without revisiting past data—is closely related to standard online/i.i.d. streaming learning and minibatch stochastic optimization, not a substantially new problem class.

The second contribution, per-chunk weight averaging, is also best viewed as an application/adaptation of known averaging ideas rather than a new algorithmic principle. Averaging learned weights/checkpoints is well established in Polyak/Ruppert averaging, exponential moving averages, stochastic weight averaging, and model soups. The paper’s specific twist is to average end-of-chunk weights in the chunking/continual-learning setting and show that this can reduce forgetting and improve accuracy. That is a potentially useful empirical observation, but it should be framed as a simple adaptation of existing weight-averaging methods to chunked continual learning rather than as a substantially novel method.

Overall, the paper contributes a clear diagnostic framing and useful empirical evidence, but the conceptual novelty of both claimed contributions is limited: “chunking” largely repackages same-distribution online/streaming learning for the continual-learning audience, and per-chunk weight averaging is a known family of methods applied at chunk boundaries.

**Impact:** weakness, C3, confidence=medium

**Evidence:**
- paper: The paper defines chunking as observing chunks sequentially, training on one chunk at a time, and not revisiting previous chunks, while all chunks are drawn from the same distribution and task shift is removed. This supports the view that the setting is essentially same-distribution streaming/batched-online learning, although framed as a reduced continual-learning setting.
- paper: The paper’s own map/related-work summary states that chunking is related to online learning without task shift, but uses batched chunks to match neural-network training. This indicates that the authors know the setting overlaps with prior online-learning formulations rather than being wholly new.
- paper: The paper claims empirical value by showing that chunking accounts for roughly half of the offline-to-continual-learning accuracy drop in selected CIFAR-100 and Tiny ImageNet experiments, and that standard continual-learning methods perform similarly to SGD in the no-task-shift chunking setting. This is the more original part: isolating and measuring this component inside CL.
- paper: For the method, the paper proposes averaging neural-network parameters at the end of each chunk and evaluating the averaged model, including mean and EMA variants. The paper also motivates this through a linear-case analysis where weight averaging is presented as a memory-limited approximation to Bayesian aggregation.
- inference: The per-chunk averaging idea is very close in spirit to established weight-averaging methods: Polyak/Ruppert averaging, EMA of weights, stochastic weight averaging, and model soups/checkpoint averaging. The paper’s novelty is therefore mainly the boundary at which averaging is applied and the empirical demonstration in chunked CL, not the averaging mechanism itself.
- inference: Because external retrieval results were not available in the tool observations, this novelty judgment relies on the paper’s own related-work positioning plus standard reviewer knowledge of online learning and weight averaging. Confidence is therefore medium rather than high.

## Soundness

### Q1

**Question:** Do the experiments report sufficient statistical reliability and fair tuning—for example, number of seeds/error bars or significance tests for the chunking and weight-averaging results, and whether baselines and weight-averaging variants were tuned under comparable validation protocols?

**Answer:** No. The paper provides some reliability information for the later continual-learning results, but the statistical support appears incomplete for the core chunking and per-chunk weight-averaging claims. The paper map indicates that Table 2 reports class-/task-incremental accuracy averaged over 3 runs with standard error, which is useful. However, the main chunking analyses and weight-averaging figures/tables are described primarily as point accuracies or curves, with no clear mention of seeds, error bars, confidence intervals, or significance tests for claims such as chunking explaining roughly half of the offline-to-CL gap or mean weight averaging improving smallest-chunk accuracy by +4.32%, +8.22%, and +11.73%. On tuning, Appendix A is reported to use grid-searched hyperparameters, but the available evidence does not establish that all baselines and weight-averaging variants were tuned under the same validation protocol, nor that validation rather than test performance guided choices such as EMA weighting. Appendix E evaluates different EMA alpha values, but this reads more like an ablation than a clearly controlled tuning protocol. This matters for soundness because several central conclusions depend on relative differences among SGD, CL baselines, and weight-averaging variants, and those differences could be sensitive to random seed variance or unequal hyperparameter selection.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper map reports that Section 7/Table 2 gives class-incremental and task-incremental accuracy averaged over 3 runs with standard error for CL methods with and without weight averaging.
- paper: The paper map describes Section 4/Table 1 and Figures 2-5 as reporting end-of-training test accuracy, offline-to-CL drop percentages, and forgetting curves, but does not indicate error bars, seed counts, or significance tests for these chunking results.
- paper: The paper map describes Section 6/Figure 6 as reporting mean weight-averaging gains of +4.32%, +8.22%, and +11.73% on CIFAR-10, CIFAR-100, and Tiny ImageNet, but does not indicate statistical tests or uncertainty estimates for these gains.
- paper: Appendix A is summarized as providing experimental details and grid-searched hyperparameters; Appendix E evaluates different EMA weighting values, but the summary does not establish a single comparable validation protocol across baselines and weight-averaging variants.
- inference: Because only some results are explicitly summarized as averaged with standard error, while the core chunking and weight-averaging claims appear to lack uncertainty reporting and significance testing, the statistical reliability is only partially supported.

### Q2

**Question:** Is the claim that “chunking explains roughly half of the offline-to-CL performance gap” methodologically well supported—i.e., is the attribution formula clearly defined, evaluated across multiple CL methods/seeds/task splits, and controlled for differences such as number of updates, data exposure, replay memory, and task-label availability?

**Answer:** No. The claim is only partially supported. The paper appears to define the attribution in a straightforward accuracy-gap way—roughly, the fraction of the offline-to-CL accuracy drop accounted for by the drop from offline to chunking—and Table 1 reports values of 50.05% on CIFAR-100 and 46.69% on Tiny ImageNet. However, the empirical basis is narrow: the “roughly half” estimate is reported for two datasets, using ResNet18 and a 10-task/chunk setup, apparently tied to DER++ for the full CL comparison. The paper does compare several CL methods in the chunking-only setting, but the specific offline-to-CL decomposition is not shown across multiple CL algorithms, multiple task splits, or with clear seed-level uncertainty. It also does not convincingly isolate the attribution from possible confounds such as different numbers of optimization updates, repeated data exposure, replay-buffer access in CL methods, and class/task-label availability between class-incremental, task-incremental, chunking, and offline regimes. Appendix analyses on chunk balance and epoch count help, but they do not fully control the central decomposition claim. Thus, the result is suggestive but not methodologically strong enough to justify a broad claim that chunking generally explains about half of the CL gap.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper summary identifies Table 1 as reporting end-of-training test accuracy and the percentage of the offline-to-CL drop attributed to chunking, with reported values of 50.05% for CIFAR-100 and 46.69% for Tiny ImageNet using DER++.
- paper: The chunking setup is defined as sequential chunks drawn from the same distribution with no task shift and no revisiting of previous chunks; experiments use balanced chunks and compare offline, chunking, and standard CL settings.
- paper: The broader chunking experiments compare plain SGD with DER++, ER, ER-ACE, AGEM, EWC, and GSS, but the specific “half of the offline-to-CL gap” attribution is summarized only for selected CIFAR-100/Tiny ImageNet comparisons rather than systematically across all methods.
- paper: The appendices include some relevant controls, such as balanced versus random chunk sampling and different numbers of epochs per chunk, but these are not described as a full control analysis for the Table 1 attribution claim across CL methods, seeds, replay settings, or task-label regimes.
- inference: Because CL methods may use replay memory, task labels, different exposure patterns, and different update schedules, a causal attribution of the offline-to-CL gap to chunking requires careful matched controls. The available evidence supports chunking as an important factor, but not a precise or general “roughly half” causal decomposition.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall / ICLR format (pp. 1–8):**
  - The paper appears to follow the ICLR submission style: correct anonymous header, page numbers, margins, section headings, and single-column layout.
  - Text is generally readable, but pages are dense with long paragraphs; quick visual inspection is somewhat slowed by compact figures/captions.
  - No major margin overflows or obvious template violations visible.

- **Figures and tables legibility:**
  - **p. 3, Figure 1:** Diagram is understandable, but some internal labels/arrow annotations are small, especially the small “Inc. chunks per task” text. Caption is clear and connected to the diagram.
  - **p. 4, Table 1:** Table is mostly legible and well aligned. However, uncertainty values in smaller font are quite small. Caption is informative but long.
  - **p. 4, Figure 2:** Plots are readable at page scale, but axis labels, tick labels, and legends are small. Multiple colored lines without markers may be hard to distinguish in print or for color-impaired readers.
  - **p. 5, Figures 3–5:** Plots are generally legible, but all legends/ticks/axis labels are small. Figure 4’s dense loss curve is visually busy. Figure 5 is clearer but still relies heavily on color.
  - **p. 7, Figure 6:** Four-panel figure is useful, but each subplot is small; legends and tick labels are hard to read. Panel labels (a)–(d) help.

- **Captions:**
  - Captions are generally informative and describe the key visual content and experimental setup.
  - **p. 5:** Figure 3 and Figure 4 captions are placed side-by-side and feel cramped; the separation between the two captions could be clearer.
  - **p. 7, Figure 6 caption:** Informative but very long; also contains a typo: “leaning” should likely be “learning.”

- **Layout / typography / formatting issues:**
  - **p. 5:** The top row with Figure 3 and Figure 4 plus adjacent captions is visually crowded; captions nearly read as a combined block.
  - **pp. 4–7:** Many plots have small default Matplotlib-style fonts; increasing plot font sizes, line widths, and/or adding markers would improve readability.
  - **p. 6:** Equations are nicely centered and numbered, but the equation block is dense. Equation (3) visually appears to repeat \(V_k^{-1}\) on both sides, which may be a notation/typographical issue worth checking.
  - **General:** Several figures depend only on color-coded lines; consider markers, line styles, or more colorblind-safe palettes.

- **Ease of visual inspection:**
  - The submission is visually inspectable and professionally formatted overall.
  - Main readability weakness is not the paper layout, but the small plot typography and dense multi-curve figures/captions. Larger plot text and less cramped caption placement would make review easier.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

# Q&A Trajectory

## Contribution

### Q1

**Question:** How novel is Soft iEP relative to prior Edge-Popup/strong lottery ticket methods and existing iterative pruning or rewinding methods? In particular, are the “dying edge/dying ratio” analysis and the soft iterative pruning procedure meaningfully new, or mostly straightforward adaptations of known lottery-ticket iterative pruning ideas?

**Answer:** Soft iEP appears only moderately novel. The paper’s most distinct contribution is not a wholly new pruning paradigm, but an empirical diagnostic for Edge-Popup: “dying edges” and the associated “dying ratio,” i.e. masked edges that are never activated during score optimization. This is a useful lens specific to gradient-based strong lottery ticket search, and the paper provides empirical evidence that high dying ratios occur and correlate with limited exploration. However, the proposed remedy—iteratively running Edge-Popup while increasing sparsity and using score/learning-rate rewinding—is largely a straightforward transfer of known lottery-ticket iterative pruning and rewinding ideas into the Edge-Popup/strong-lottery-ticket setting.

The “soft” part is a meaningful but incremental modification: unlike hard iterative pruning, Soft iEP does not permanently restrict later cycles to the previously retained mask; it keeps the original search space available while inheriting learned scores and increasing the pruning ratio. This addresses the paper’s own false-negative dying-edge concern, but conceptually it is close to gradual pruning / iterative pruning with rewinding, except applied to mask-score optimization rather than weight training. Therefore, the contribution is best characterized as an application and empirical analysis of established LTH-style iterative pruning/rewinding mechanisms to Edge-Popup, plus a new diagnostic metric, rather than a fundamentally new algorithmic idea.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper defines the strong lottery ticket / Edge-Popup setup: weights are fixed at initialization, each edge has a trainable score, and the top-scored edges under a pruning ratio form the subnetwork. This directly builds on prior Edge-Popup strong lottery ticket methods rather than replacing them.
- paper: Section 3 introduces “dying edges” and “dying ratio” as an empirical measure of exploration inefficiency: edges that are masked and never selected during Edge-Popup optimization. The paper reports, for example, that on CIFAR-10 ResNet18 the dying ratio increases substantially with pruning ratio, from about 0.028 at k=0.200 to about 0.656 at k=0.832.
- paper: Section 4 explicitly frames hard iEP as iterative pruning in the Edge-Popup setting, with variants corresponding to fine-tuning, score rewinding, score reinitialization, and learning-rate rewinding. Soft iEP then modifies this by inheriting scores, increasing the pruning ratio over cycles, resetting the learning rate by default, and keeping the original full search space rather than permanently pruning earlier low-score edges.
- paper: The conclusion states that testing iterative pruning variants in the strong lottery ticket setting provides a methodological connection between lottery tickets and strong lottery tickets, and lists lack of theoretical explanation for dying edges and Soft iEP’s success as a limitation. This supports an interpretation of the work as empirical/diagnostic and adaptation-oriented rather than theoretically or algorithmically fundamental.
- retrieval: Ramanujan et al. introduced Edge-Popup for finding high-performing subnetworks in randomly initialized fixed-weight networks, establishing the main strong lottery ticket search mechanism that Soft iEP extends.
- retrieval: Frankle and Carbin introduced the Lottery Ticket Hypothesis and iterative magnitude pruning with resetting/rewinding ideas; later work such as Frankle et al. and Renda et al. studied rewinding and fine-tuning choices. Soft iEP’s iterative cycles, increasing sparsity, and rewinding-style variants are closely aligned with these prior ideas.
- inference: The novelty judgment is that the dying-ratio diagnostic is relatively more novel in the Edge-Popup context, while the Soft iEP optimization procedure is mostly an expected adaptation of iterative pruning/rewinding to score-based mask search. The full-search-space “soft” choice is a useful engineering distinction from hard iEP but not a major conceptual departure from gradual/iterative pruning principles.

**Retrieved Papers:**
- What’s Hidden in a Randomly Weighted Neural Network? | 2020 | https://arxiv.org/abs/1911.13299 | Introduces Edge-Popup and the empirical strong lottery ticket setting that Soft iEP directly extends.
- The Lottery Ticket Hypothesis: Finding Sparse, Trainable Neural Networks | 2019 | https://arxiv.org/abs/1803.03635 | Introduces iterative pruning and resetting ideas for lottery tickets; Soft iEP follows this broad iterative-pruning template.
- Linear Mode Connectivity and the Lottery Ticket Hypothesis | 2020 | https://arxiv.org/abs/1912.05671 | Part of the rewinding literature showing that resetting/rewinding to early training states is important in lottery ticket methods, conceptually related to Soft iEP’s rewinding-style variants.
- Comparing Rewinding and Fine-tuning in Neural Network Pruning | 2020 | https://arxiv.org/abs/2003.02389 | Studies pruning variants such as fine-tuning and rewinding; relevant because the Soft iEP paper adapts similar variant comparisons to Edge-Popup score optimization.

## Soundness

### Q1

**Question:** Do the experiments report statistical reliability details such as number of random seeds/runs, error bars or standard deviations, and are the main EP/hard iEP/Soft iEP comparisons matched for compute budget and hyperparameter tuning?

**Answer:** No. The experimental reporting appears weak on statistical reliability: the summarized experimental sections report point estimates for accuracy and dying ratio, but do not indicate numbers of random seeds/runs, error bars, confidence intervals, or standard deviations for the main EP, hard iEP, and Soft iEP comparisons. The compute-budget matching is also not established. Soft iEP is explicitly an iterative method that reapplies Edge-Popup across pruning cycles, and the paper itself lists increased search time as a limitation, implying the main gains over one-shot EP are not shown under equal compute. Hard iEP and Soft iEP are compared as iterative variants, but the paper summary does not indicate that all methods receive matched total optimization steps, wall-clock budget, or equivalent hyperparameter tuning. This matters for soundness because the reported Soft iEP improvements over EP/hard iEP could partly reflect additional search computation or tuning rather than the proposed soft-pruning mechanism alone, and the lack of variance estimates makes it hard to judge whether reported accuracy differences are statistically reliable.

**Impact:** weakness, C3, confidence=medium

**Evidence:**
- paper: The experiments are described as reporting test accuracy, parameter count/remaining ratio, and dying ratio across ImageNet, CIFAR-10, and CIFAR-100, with results such as Soft iEP outperforming EP and hard iEP; the paper map does not identify any reported seed count, standard deviation, confidence interval, or error-bar information.
- paper: The method description states that Soft iEP applies EP iteratively with increasing pruning ratio while keeping the original search space available; hard iEP is also iterative, while EP is the one-shot baseline.
- paper: The limitation section explicitly states that Soft iEP increases search time because EP is applied iteratively.
- inference: Because Soft iEP performs repeated EP cycles and the paper acknowledges increased search time, the main EP-vs-Soft-iEP comparison is not demonstrated to be compute-matched unless the paper separately controls total search steps or wall-clock budget; no such control is evident from the provided experimental map.
- inference: Without random-seed counts or variance/error-bar reporting, accuracy gains such as the reported 1--2 point improvements cannot be assessed for statistical reliability.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** Extracted PDF text:
Page 1:
Under review as a conference paper at ICLR 2024
SOFT I EP: O N THE EXPLORATION INEFFICACY OF
GRADIENT -BASED STRONG LOTTERY EXPLORATION
Anonymous authors
Paper under double-blind review
ABSTRACT
Edge-popup (EP) is a de facto algorithm to find strong lottery tickets (SLT), the
sparse subnetworks that achieve high performance without weight updates. EP
finds the subnetworks by optimizing a score vector representing the importance
of each edge, and selects subnetworks given optimized scores. This paper first
shows that such a simple gradient-based method results in a suboptimal solution
due to the existence of dying edges. Specifically, we show that most edges are
never selected during the search process, i.e., EP might be trapped around the local
minima nearby random subnetworks and need help to search the entire spaces of
subnetworks effectively. We then propose asoft iterative edge-pop (Soft iEP) as a
simple mechanism to better explore search spaces. Unlike the standard iterative
pruning that masks out a certain amount of edges and thus induces a similar
problem to the dying edges, Soft iEP do not disable the bottom edges at each
cycle, i.e., leave a chance to be selected at the end regardless of whether it was
chosen at the former cycle. Empirical validations show that iEP with soft pruning
stably outperforms both EP and iEP w/ hard pruning on ImageNet, CIFAR-10, and
CIFAR-100 and reduces dying edges. Our results also provide new insight into
why iterative pruning helps to find good sparse networks.
1 I NTRODUCTION
Ramanujan et al. (2020); Chijiwa et al. (2021); Yeo et al. (2023) demonstrated that a randomly
initialized neural network contains sparse subnetworks that achieve comparable performance with
fully-trained dense networks. For example, Ramanujan et al. (2020) shows that randomly initialized
WideResNet50 contains subnetworks that achieve comparable performance to trained ResNet34
without updating weights. Such sparse networks are called as strong lottery tickets (SLT), since it
shares the core concept with lottery tickets hypothesis (Frankle and Carbin, 2019) in a sense that both
suggest a randomly initialized over-parameterized networks contain subnetworks that attain good
properties. It has been raising attention on the phenomenon of SLT, not only its intriguing property
of the overparameterized random networks (Du et al., 2018; Allen-Zhu et al., 2019), but also several
practical benefits including that (1) SLT is robustness to the binarization or quantization and weights
to save the memory footprint (Diffenderfer et al., 2021; Diffenderfer and Kailkhura, 2021), and (2)
unlearned weight can be reconstructed only by storing random seed and binary masks (Okoshi et al.,
2022). Hirose et al. (2022) proposed specialized hardware to accelerate inference using the property.
Many subsequent works support the existence of SLT, both empirically (Ramanujan et al., 2020;
Chijiwa et al., 2021; Sreenivasan et al., 2022; Yeo et al., 2023) and theoretically (Malach et al., 2020;
Pensia et al., 2020; Orseau et al., 2020; Burkholz, 2022; da Cunha et al., 2022). Although the problem
of discovering a good subnetwork can be naturally cast as a combinatorial optimization (Korte et al.,
2011), it is usually intractable given a huge number of parameters. Instead, most prior methods
rely on edge-pop (EP) algorithm (Ramanujan et al., 2020), which cast the structure search as a
sort of stochastic optimization. Specifically, EP first assigns a real-valued score for each edge and
updates its score via the loss calculated using subnetworks selected based on the scores (e.g., by a
threshold). Prior studies show that EP can find SLT that is comparable with fully-trained networks
on various model sizes (from small conv to wide ResNet), datasets (including ImageNet), and tasks
(classification and generation (Ramanujan et al., 2020; Yeo et al., 2023)).
1

Page 2:
Under review as a conference paper at ICLR 2024
Figure 1: Visualization of the d...

VLM page observations:
- **Overall / all pages**
  - Uses recognizable ICLR single-column formatting with page numbers and review header; generally easy to follow visually.
  - Major presentation issue: extensive **red text** appears throughout pages 1, 3–8, including captions, paragraphs, equations/table rows. This looks like revision markup or author notes and is distracting/unpolished for a submission.
  - Text density is high on most pages; readability is acceptable but some pages feel crowded, especially around tables and multi-panel plots.

- **Page 1**
  - No figures/tables. Abstract and title are readable.
  - Red paragraph text in the introduction is visually jarring and inconsistent with the rest of the manuscript.

- **Page 2 — Figure 1**
  - Figure is mostly legible; color/pattern coding helps distinguish edge types.
  - Some small labels/legend text may be hard to read at print size.
  - Caption is informative and directly explains colors, edge types, and dying ratio.

- **Page 3**
  - Equation (1) is centered, numbered, and readable.
  - Red inline mathematical/text additions disrupt the otherwise clean typography.

- **Page 4 — Figure 2 / Equation (2)**
  - Figure 2 is legible and visually connected to the caption; gray background and color coding work reasonably well.
  - Caption clearly explains true negative vs. false negative dying edges.
  - Equation (2) is readable, but surrounding red text and red equation coloring look like markup rather than final formatting.

- **Page 5 — Tables 1–2**
  - Table 1 is small but legible.
  - Table 2 is dense but still readable; bold values help.
  - Table 2 caption is overly long and entirely red, which reduces professionalism and visual clarity.
  - Large red explanatory paragraph below the tables is distracting.

- **Page 6 — Table 3**
  - Table 3 is legible, though dense with mathematical notation.
  - Caption is detailed and connected to the table content.
  - Red rows/caption fragments again appear like revision markup and make the table look inconsistent.

- **Page 7 — Figure 3**
  - Figure 3 conveys the intended comparisons, but the subplots are small; axis labels, tick labels, and legends are difficult to read without zooming.
  - Caption is informative and connected to the plots.
  - There is substantial blank space above the figure, suggesting float/layout inefficiency.
  - Long red note at the bottom makes the page visually heavy.

- **Page 8 — Figure 4**
  - Plots are generally interpretable, but legends and x-axis tick labels are small/crowded.
  - Caption is informative, but much of it is red and quite long.
  - Page is text-heavy after the figure; visual inspection is harder due to dense paragraphs and color inconsistency.

- **Summary**
  - Figures/tables are mostly legible, but several plots would benefit from larger fonts and less crowded legends/ticks.
  - Captions are generally informative and well connected to visuals, though some are too long.
  - Main formatting concern is pervasive red text/markup, which significantly hurts presentation quality for an ICLR submission.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_text:P1-P3
- pdf_image:vlm_pages

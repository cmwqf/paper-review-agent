# Q&A Trajectory

## Contribution

### Q1

**Question:** How novel is FLAVA relative to prior work such as TVLT/CAV masked audio-video learning, AV-CIL/IncCLIP multimodal continual learning, DER++ rehearsal, and existing attention/patch-selection methods? In particular, is the main contribution a genuinely new task setting/method, or mostly an adaptation/combination of known continual learning and audio-video masking ideas?

**Answer:** FLAVA appears moderately novel, but its contribution is closer to an adaptation and integration of known ideas than a fundamentally new method. The paper's strongest novelty claim is the task setting: task-free continual self-supervised audio-video representation learning under shifting audio-video data distributions, where prior masked audio-video learners such as TVLT/CAV are positioned as assuming a fixed distribution, and prior multimodal continual methods such as AV-CIL/IncCLIP are positioned as relying on labels or task-boundary information. Methodologically, however, FLAVA combines familiar components: masked audio-video reconstruction/contrastive pretraining, attention-derived patch importance, rehearsal memory, and a DER++-style consistency penalty. The more specific new ingredient is the use of current-versus-memory cross-modal attention to select “forget-robust” localized audio/video patches. That is a plausible incremental contribution, but not a clearly paradigm-shifting one. For contribution assessment, I would characterize FLAVA as a useful specialization of masked audiovisual learning plus rehearsal-based continual learning to a task-free audiovisual setting, rather than a genuinely new continual-learning principle.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper positions TVLT and CAV as prior masked audiovisual representation-learning methods and states that such methods assume a fixed input distribution, while FLAVA targets continually changing audio-video streams.
- paper: The paper positions IncCLIP and AV-CIL as multimodal continual-learning methods, but distinguishes FLAVA by claiming that these prior approaches require dense labels or task-boundary information, whereas FLAVA is task-free and self-supervised.
- paper: Section 3 formalizes continual audio-video pretraining over a sequence of disjoint unsupervised datasets without explicit task-boundary knowledge, using masked reconstruction and masked contrastive objectives.
- paper: Section 4 describes FLAVA's method as an Audio-Video Matching module producing cross-modal attention maps, importance scores from mean-pooled attention, a forget-robust pruning probability comparing current and past memory queries, audio/video patch selection, and a final objective including a DER++-style memory penalty loss.
- paper: The reproducibility statement says the implementation is based on RepLAI, TVLT, and CAV, further suggesting that the core architecture and masked audio-video training framework build on existing systems.
- retrieval: No external retrieved papers were provided in the current evidence. The available tool observation reports no matches for a combined in-paper query over “TVLT CAV IncCLIP AV-CIL DER++ novel task-free continual audio-video,” so this judgment relies mainly on the reviewed paper's own positioning and method description rather than independent full-paper comparison.
- inference: Because FLAVA's components map onto known families—masked audiovisual pretraining, attention-based token/patch selection, rehearsal memory, and DER++-style regularization—the novelty is best viewed as the audiovisual task-free continual formulation plus a tailored patch-selection heuristic, not as a wholly new learning framework.

## Soundness

### Q1

**Question:** Does the paper report results over multiple random seeds or provide standard deviations/significance tests, especially for the small retrieval gains over baselines such as the 0.03%p and 0.58%p improvements on AudioSet? Also, are baselines tuned/run under comparable memory and compute budgets?

**Answer:** The paper appears weak on statistical support. The reported retrieval tables present single-point R@K/average-accuracy values and the paper summary identifies very small AudioSet gains for FLAVA over the strongest baseline, including only 0.03 percentage points for audio-to-video retrieval and 0.58 percentage points for video-to-audio retrieval. I found no indication in the provided paper text/map that these retrieval results are averaged over multiple random seeds, accompanied by standard deviations, confidence intervals, or significance tests. This makes the smallest claimed gains difficult to interpret as robust improvements rather than noise from initialization, task order, sampling, or evaluation variance. On compute comparability, the paper does report an efficiency comparison with GPU memory and throughput, e.g. FLAVA at 17.45 GB and 17.43 samples/sec versus DER++ at 30.95 GB, which is useful. However, that does not by itself establish that all baselines were equally tuned or constrained under comparable training compute, memory, hyperparameter-search budgets, or rehearsal-memory settings. The appendix reportedly includes hyperparameter tuning studies, but the available evidence does not show a clear protocol ensuring comparable tuning budgets for baselines. Overall, this is an important soundness weakness because some headline gains, especially on AudioSet retrieval, are too small to be convincing without uncertainty estimates and matched baseline tuning/compute controls.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The experiment summary reports AudioSet retrieval gains of only 0.03%p for audio-to-video and 0.58%p for video-to-audio for FLAVA over baselines.
- paper: The paper reports retrieval results using R@K and continual-learning average accuracy/forgetting in Table 1, but the provided map does not mention multiple random seeds, standard deviations, confidence intervals, or significance tests.
- paper: The paper reports an efficiency table with GPU memory and throughput, including FLAVA using 17.45 GB GPU memory and 17.43 samples/sec, compared with DER++ using 30.95 GB.
- paper: The appendix includes some hyperparameter tuning analyses, such as memory size, task order, sampling ratios, and AVM temperature, but the available evidence does not show a matched hyperparameter-search or compute-budget protocol for all baselines.
- inference: Because the smallest reported improvements are far below one percentage point, lack of variance estimates or significance testing materially weakens confidence that these are reproducible improvements. Efficiency reporting is helpful but insufficient to prove fair baseline tuning and compute comparability.

### Q2

**Question:** Do the ablations and baseline comparisons cleanly isolate FLAVA’s claimed contributions from other factors, especially with a matched DER++ baseline using the same loss and memory budget but without FLAVA patch selection?

**Answer:** No. The paper provides useful but incomplete isolation. It compares against DER++ and includes patch-selection ablations such as Random, MATS, LAVA-only, FRS-only, and full FLAVA, which helps test whether the proposed localized alignment and forget-robust selection matter. However, the evidence does not show a fully matched control that uses the same DER++-style objective, same rehearsal budget/content format, same backbone/pretraining setup, and same added AVM parameterization while simply disabling FLAVA’s learned patch selection. The DER++ baseline is the closest comparison, but FLAVA’s own objective includes a DER++-style memory penalty, while FLAVA/FLAVA+ also change patch/token selection and, for FLAVA+, memory contents. Efficiency results also show large memory differences between DER++ and FLAVA, suggesting that the comparisons are not fully matched in computational or memory behavior. Thus, the ablations support that LAVA and FRS are beneficial, but they do not cleanly rule out confounds from DER++ loss usage, replay-memory construction, AVM parameters, or token-budget differences.

**Impact:** weakness, C3, confidence=medium

**Evidence:**
- paper: Section 4.3 describes FLAVA’s final objective as combining reconstruction loss, masked contrastive loss, and a DER++-style memory penalty loss.
- paper: Section 5.1 lists continual-learning baselines including ER, MIR, DER++, GMED, CLS-ER, LUMP, Finetune, and Multitask.
- paper: Table 3 ablates patch-selection variants: Random, MATS, LAVA-only, FRS-only, and full FLAVA, with full FLAVA giving the best reported VGGSound retrieval averages among these variants.
- paper: Section 4 introduces extra FLAVA machinery, including an Audio-Video Matching module for localized alignment and a forget-robust pruning probability based on current and memory attention.
- paper: Table 2 reports different GPU memory usage between DER++ and FLAVA, with DER++ at 30.95 GB and FLAVA at 17.45 GB, indicating that the compared methods are not identical in resource behavior.
- paper: The paper distinguishes FLAVA+ as storing selected patches rather than raw data in memory, which changes rehearsal memory contents relative to standard replay-style baselines.
- inference: Because the paper does not clearly report a control that keeps DER++ loss, replay budget, AVM parameters, backbone/pretraining objective, and token/memory handling fixed while disabling only FLAVA patch selection, the claimed gains cannot be attributed solely to localized alignment and forget-robust selection with high causal precision.

### Q3

**Question:** For the claimed task-free continual setting, does FLAVA or any baseline require task-boundary information, class labels, or task-balanced memory/evaluation during training, and is the stream construction realistic enough to support the “without task identification” claim?

**Answer:** FLAVA appears not to use class labels or task IDs as inputs to its representation-learning objective: the core training is self-supervised masked reconstruction/contrastive learning, plus an audio-video matching/localized-alignment module and rehearsal-style memory. The listed continual baselines also seem to be adapted to the same self-supervised setting rather than using class-label supervision. However, the experimental protocol is not fully “task-free” in the strongest sense. The stream is constructed from explicit class/category-based tasks: VGGSound is split into 8 tasks and AudioSet into 7 tasks based on class hierarchy. Training and evaluation are organized around these discrete tasks, and metrics such as average accuracy and average forgetting are computed per task. Thus, while the model may not be given a task identifier at inference/training time and may not use class labels in the loss, the benchmark construction relies on task/class information and known task partitions. I found no clear evidence that memory is explicitly class-balanced, but the rehearsal memory and evaluation are embedded in a task-structured protocol. This makes the “without task identification” claim only partially supported: it is valid as “no task ID is fed to the model,” but less convincing as a realistic task-free video stream, because the distribution shifts are artificially induced by labeled category splits and task-wise evaluation.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: Section 3.1 is summarized as defining task-free continual pre-training over a sequence of disjoint unsupervised audio-video datasets “without explicit knowledge of task boundaries.”
- paper: Section 5 reports task-wise continual-learning metrics, including average accuracy and average forgetting, for zero-shot retrieval and audiovisual classification.
- paper: The appendix split description states that VGGSound is split into 8 tasks and AudioSet into 7 tasks based on class hierarchy, indicating that labels/categories are used to construct the continual stream.
- paper: The method uses masked reconstruction, masked contrastive learning, localized audio-video alignment, and a DER++-style memory penalty; no paper-summary evidence indicates use of class labels in FLAVA’s training loss.
- inference: Because the benchmark is built from labeled class/category task partitions and evaluated with per-task forgetting/accuracy, the setup depends on task structure at the protocol level even if the model itself is not given task IDs. This weakens the realism of the strongest “task-free” or “without task identification” framing.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall ICLR visual style:** Pages use the ICLR review header, page numbers, margins, and single-column formatting consistently. The paper is generally easy to visually inspect, but several visuals are quite dense.

- **Figures legibility**
  - **p.2, Fig. 1:** Mostly legible; video frames and spectrogram are small but understandable. Timeline labels are readable.
  - **p.2, Fig. 2:** Conceptually clear, but the subpanels, heatmaps, and orange-circle annotations are small; fine details are hard to inspect at page scale.
  - **p.4, Fig. 3:** Wide figure is readable overall, but internal frame details and heatmap distinctions are small. Caption is connected to the panels.
  - **p.5, Fig. 4:** The overview diagram is visually useful but overcrowded; many internal labels and arrows are too small to read comfortably.

- **Tables / algorithms**
  - **p.7, Algorithm 1:** Mostly readable and well structured with shaded regions, but dense. Title has a typo: “Foget-robust” should be “Forget-robust.” The lowercase “input” is stylistically inconsistent with typical algorithm formatting.
  - **p.8, Table 1:** Legible but very dense; many columns, small font, and nested headers make it difficult to scan quickly. Caption is informative and explains bold/underline conventions.

- **Captions**
  - Captions are generally informative and explicitly tied to visual content.
  - **p.2, Fig. 2 caption:** Contains a punctuation issue: “maps.:” should be “maps:”.
  - **p.5, Fig. 4 caption:** Helpful but long; colored emphasis in the caption is visually distracting.

- **Typography / color / formatting**
  - Large amounts of **orange text** on pp.5–7 and **blue emphasis** on p.8 look like revision highlighting rather than final paper formatting; this is distracting and reduces polish.
  - Red figure/equation references and green citations are common with hyperref, but combined with orange/blue highlights the page becomes visually busy.
  - Some paragraphs have heavy inline math and symbols, making pages 5–6 visually dense.

- **Equations**
  - Equations are generally readable and numbered consistently.
  - **p.5, Eq. 4:** Very compressed multi-line equation block; hard to parse visually due to many indices and hats. Consider splitting or adding spacing.
  - **p.6, Eqs. 5–7:** More readable, though surrounded by dense highlighted text.

- **Layout**
  - **p.2:** Figure 2 is placed beside text with a narrow caption; acceptable, but it makes both the figure and caption feel cramped.
  - **p.5:** Fig. 4 spans the page well, but its internal content is too small for comfortable inspection.
  - **p.8:** Table appears before the surrounding explanation completes, but placement is acceptable.

- **Bottom line:** The submission is broadly inspectable as an ICLR paper, with consistent structure and informative captions. Main presentation concerns are overcrowded figures, very dense Table 1, distracting colored/highlighted text, and a few caption/algorithm typos.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

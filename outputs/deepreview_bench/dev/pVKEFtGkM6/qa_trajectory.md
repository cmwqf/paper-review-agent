# Q&A Trajectory

## Contribution

### Q1

**Question:** What prior work most directly studied calibration/overconfidence of aligned or instruction-tuned language models in multiple-choice settings, and how does this paper's contribution differ from or extend those works?

**Answer:** The most directly relevant prior work appears to be work showing that large LMs can be calibrated on multiple-choice or QA tasks, especially Kadavath et al.'s “Language Models (Mostly) Know What They Know,” together with reports such as the GPT-4 Technical Report showing that post-training/RLHF can make an otherwise calibrated model overconfident. Earlier calibration work on LMs and few-shot prompting, such as contextual calibration and temperature-scaling-style methods, is also relevant but less directly about aligned or instruction-tuned models.

This paper’s contribution is not simply the observation that aligned models are overconfident. Its main extension is a more targeted empirical and mechanistic study of multiple-choice logit-based calibration for aligned LMs: it compares pre-trained Llama/Llama-2 models against aligned Vicuna/Llama-2-Chat models across several MCQ tasks; separates “answer uncertainty” from “format uncertainty”; studies SFT/LPF and synthetic alignment variants to argue that alignment changes answer uncertainty rather than merely making models prefer the requested output format; and proposes a few-shot post-hoc calibration method that matches the aligned model’s temperature-scaled predictive distribution to that of the corresponding pre-trained model. Thus, relative to prior work that mostly documented calibration or miscalibration, this paper tries to explain a specific source of overconfidence in aligned MCQ answering and offers a targeted mitigation. The novelty is meaningful but incremental: the core phenomenon was already known, while the decomposition/controlled alignment analysis and pre-trained-counterpart calibration objective are the main differentiators.

**Impact:** strength, C2, confidence=medium

**Evidence:**
- paper: The paper summary states that the introduction motivates the work by noting that aligned LMs are often more overconfident than their pre-trained counterparts, and that the paper’s goals are to compare calibration behavior, analyze alignment effects through two uncertainties, and propose a few-shot post-hoc calibration method.
- paper: Section 3, according to the paper map, evaluates pre-trained Llama/Llama-2 models against aligned Vicuna/Llama-2-Chat models on seven multiple-choice tasks and finds that aligned LMs have higher ECE than corresponding pre-trained models and remain overconfident under both zero-shot and in-context learning.
- paper: Section 4 defines answer uncertainty and format uncertainty, decomposes the predictive probability into answer probability conditioned on format and format probability, and uses SFT/LPF checkpoints plus synthetic SFT/DPO variants to argue that changing answer uncertainty during alignment is a main contributor to overconfidence.
- paper: Section 5 proposes a few-shot post-hoc calibration method that learns a task-specific temperature by minimizing KL divergence between the aligned LM’s scaled predictive distribution and the corresponding pre-trained LM’s predictive distribution; the paper also notes limitations, including the need to access the pre-trained counterpart and the assumption that it is well calibrated.
- retrieval: No external scholarly retrieval results were provided in the available tool observations, so the identification of specific prior papers is based on reviewer knowledge rather than verified retrieval in this session.
- inference: The closest prior-art positioning is that prior work had already studied LM calibration and had reported that post-training/alignment can worsen calibration, but this paper contributes a more detailed MCQ-specific analysis of why aligned models become overconfident and a calibration procedure exploiting the pre-trained counterpart.

### Q2

**Question:** Is the paper’s answer-uncertainty versus format-uncertainty decomposition a genuinely novel conceptual contribution, or is it mostly a reframing of known prompt/format sensitivity and choice-token calibration issues in multiple-choice LM evaluation?

**Answer:** The decomposition appears to be a modest conceptual contribution rather than a clearly novel one. The paper’s useful contribution is to name and operationalize two factors in MCQ logit calibration—answer uncertainty, i.e. uncertainty among candidate choices, and format uncertainty, i.e. uncertainty about emitting the expected response format—and then use this framing to analyze alignment effects through controlled SFT/DPO-style experiments. However, the decomposition itself is essentially a probability factorization of choice prediction into a format component and a conditional answer component, and the empirical proxies are closely tied to already familiar MCQ evaluation issues: prompt/format sensitivity, choice-letter token probabilities, and calibration of the maximum-probability label token. Thus, unless external retrieval shows stronger prior-art separation than available here, I would treat the decomposition as a helpful reframing and diagnostic lens, not as a major new conceptual advance.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper defines answer uncertainty as choosing among candidates and format uncertainty as preference over response formats, with the predictive probability decomposed into answer probability conditioned on format times format probability. This is central to Section 4.1.
- paper: The paper operationalizes format uncertainty using choice-format manipulations such as "A" versus "(A)" and, for the "(A)" format, the probability of the format identifier "(". This links the proposed concept directly to prompt/format sensitivity in MCQ prompting.
- paper: The main empirical support for the decomposition comes from alignment-stage and synthetic-alignment analyses: format-only synthetic alignment preserves calibration close to pre-trained ICL, while choice/mixed alignment induces overconfidence. This makes the framework useful for diagnosing alignment-induced calibration changes.
- paper: The related-work summary already acknowledges prior logit-based work finding that large pre-trained LMs can be calibrated while aligned LMs are overconfident on MCQs, suggesting the paper is building on an existing calibration/choice-token evaluation literature rather than opening an entirely new problem area.
- retrieval: No external scholarly retrieval results were provided in the available tool observations, so I cannot conclusively verify whether an identical answer/format decomposition appeared in prior work. This lowers confidence in the novelty judgment.
- inference: Because the decomposition is based on separating response-format probability from conditional choice probability, and because its measurement depends on known label-token and prompt-format artifacts, the conceptual novelty is limited. The stronger contribution is the empirical use of this framing to isolate alignment effects.

### Q3

**Question:** How practically significant and broadly applicable is the proposed few-shot post-hoc calibration method, given that it requires access to the aligned model’s pre-trained counterpart and is evaluated mainly in multiple-choice logit-based settings?

**Answer:** The method appears practically useful within a fairly narrow deployment regime, but its broader applicability is limited. Its practical value is that it uses only a few task-specific examples and learns a simple temperature parameter by matching the aligned model’s predictive distribution to that of its pre-trained counterpart; the paper reports that this outperforms out-of-the-box calibration on all evaluated tasks and is usually better than few-shot temperature scaling, KDE, or a constant temperature baseline. However, this contribution is constrained by two important assumptions: users must have access to the corresponding pre-trained base model, and that base model must itself be well calibrated on the target task. This is a substantial practical limitation for many real-world aligned LMs, especially closed models or models whose exact base checkpoint is unavailable. In addition, the evidence is mainly for multiple-choice, logit-based prediction over choice tokens, so the method is not yet shown to transfer to open-ended generation, semantic uncertainty, API-only settings without logits, or broader calibration needs. Thus, the contribution is meaningful as a targeted post-hoc calibration technique for open-weight aligned/base model pairs in MCQ-style classification, but it should not be viewed as a broadly general calibration solution.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: The paper states: “our proposed method is the only one that outperforms out-of-the-box calibration on all tasks and calibrates the language model most effectively in most scenarios,” supporting practical effectiveness in the evaluated setting.
- paper: The same passage explicitly limits the method: “our method requires access to the pre-trained counterpart of the aligned LM and relies on its strong calibration performance across various tasks, which may not be the case for all pre-trained LMs.”
- paper: The described evaluation setting is multiple-choice and logit-based: predictions and confidence are computed from choice-letter token probabilities, and the post-hoc method is evaluated on MCQ-style tasks such as MMLU, HellaSWAG, OpenbookQA, TruthfulQA, LogiQA, CivilComments, and IMDB.
- inference: Because many practical aligned LMs are served through APIs without full logits or without access to the exact pre-trained counterpart, the method’s deployability is materially narrower than a generic calibration method. Its validation also does not establish applicability to open-ended natural-language generation or semantic uncertainty calibration.

## Soundness

### Q1

**Question:** Do the experiments report statistical uncertainty or significance tests for ECE/accuracy comparisons, especially for the claimed improvements of the proposed calibration method?

**Answer:** No. The paper appears to report point estimates for accuracy, confidence, and ECE, but does not report confidence intervals, standard errors, standard deviations across seeds/prompts/samples, or statistical significance tests for the ECE/accuracy comparisons. This is especially relevant for the proposed few-shot post-hoc calibration method, because the calibration set is very small—five hold-out examples per task—yet the claimed improvements are presented as direct ECE comparisons rather than uncertainty-aware estimates. The appendices include some prompt-sensitivity analyses, but these do not appear to be used to quantify statistical uncertainty for the main calibration claims.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper defines calibration using ECE with 10 equal-sized bins and reports accuracy/confidence/ECE as empirical metrics, but the described metric setup is based on point estimates rather than confidence intervals or hypothesis tests.
- paper: The post-hoc calibration section compares few-shot temperature scaling, KDE, constant temperature scaling, and the proposed KL-to-pretrained objective using five hold-out examples per task, with results summarized as task-level ECE improvements.
- paper: The paper map indicates prompt sensitivity analyses in the appendix and full post-hoc calibration tables, but does not indicate reported standard errors, confidence intervals, seed variation, or significance testing for the main ECE/accuracy improvements.
- inference: Because ECE can be noisy—particularly with small calibration sets, prompt choices, and finite evaluation samples—the absence of uncertainty estimates weakens the evidential support for claims that the proposed calibration method reliably improves over baselines across tasks.

### Q2

**Question:** Is the key assumption that the corresponding pre-trained LM is well-calibrated under the MCQ setting empirically validated across all evaluated tasks/model sizes, and are there cases where this assumption fails or weakens the proposed calibration method?

**Answer:** The assumption is only partially validated. The paper provides empirical support that pre-trained LMs can be relatively well-calibrated in the MCQ setting, especially with five-shot in-context examples and at larger scales, but it does not establish this uniformly across all tasks, model sizes, or prompting regimes. The evidence summarized for Figure 3 indicates that pre-trained LMs have much lower ECE with larger capacity and few-shot ICL, while zero-shot settings and smaller models show weaker calibration. This means the central premise behind the proposed KL-to-pretrained post-hoc calibration method is strongest for large, ICL-conditioned pre-trained counterparts, not generally proven for every evaluated pre-trained LM. The paper itself also states this as a limitation: the method requires access to the aligned model's pre-trained counterpart and relies on that counterpart having strong calibration across tasks, which may not hold for all pre-trained LMs. As a result, there are plausible failure cases: if the pre-trained counterpart is poorly calibrated on a task, model size, or prompt format, the proposed method may match the aligned model to a flawed target distribution and thereby weaken or miscalibrate rather than improve it. The reported post-hoc results are encouraging for Llama-2-Chat 70B across the evaluated tasks, but they do not fully validate the assumption across all model sizes and settings studied earlier in the paper.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: Section 4 introduces Assumption 4.1: after eliminating format uncertainty toward the MCQ format, the pre-trained LM's answer uncertainty is assumed to be well-calibrated.
- paper: Section 3 results summarized for Figure 3 report that pre-trained LMs show substantially lower ECE with larger capacity and with five-shot in-context learning, while calibration gaps between zero-shot and ICL are especially large for larger models. This supports the assumption conditionally, not universally.
- paper: Section 5 proposes learning a task-specific temperature by minimizing KL divergence between the aligned LM's temperature-scaled predictive distribution and the corresponding pre-trained LM's predictive distribution.
- paper: The stated limitations note that the proposed method requires access to the aligned LM's pre-trained counterpart and relies on strong calibration of that pre-trained LM across tasks, which may not hold for all pre-trained LMs.
- inference: Because the proposed calibration objective treats the pre-trained model distribution as the target, any task/model-size/prompt setting where the pre-trained model is not well-calibrated directly undermines the soundness of the calibration target.

### Q3

**Question:** Do the post-hoc calibration experiments evaluate the proposed KL-to-pretrained method across multiple aligned model families/sizes and compare against sufficiently strong calibration baselines using the same few-shot calibration budget, or are the main results limited to a narrow setting?

**Answer:** The main post-hoc calibration results appear limited to a narrow setting. The proposed KL-to-pretrained temperature-scaling method is evaluated primarily on Llama-2-Chat 70B, rather than across multiple aligned model families such as Vicuna, Alpaca-Farm, Zephyr, or multiple model sizes. The paper does compare against relevant post-hoc calibration baselines—few-shot temperature scaling, KDE calibration, and a constant-temperature baseline—and these are described as using the same small calibration budget of five hold-out examples per task. However, because the central positive result is reported for one aligned model family/size, the evidence is not sufficient to establish that the proposed method generalizes broadly across aligned LMs. This limits the soundness of the calibration-method claim: the baseline comparison is useful, but the model-coverage aspect is weak.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: Section 5 proposes a few-shot post-hoc calibration method that learns a task-specific temperature by minimizing KL divergence between the temperature-scaled aligned LM distribution and the corresponding pre-trained LM distribution.
- paper: The reported main result for the post-hoc method is on Llama-2-Chat 70B, where the method is said to improve out-of-the-box calibration on all evaluated tasks and outperform or match alternatives in most scenarios.
- paper: The baselines listed for the post-hoc experiment are few-shot temperature scaling, KDE calibration, and a constant temperature T = 2.5; the calibration setting uses five hold-out examples per task.
- inference: Although earlier parts of the paper analyze multiple model families and sizes, the post-hoc method itself is not shown to work across that same range. This makes the method-level empirical support narrower than the broader diagnostic analysis.

### Q4

**Question:** Does the paper adequately justify and validate the answer/format uncertainty decomposition and the use of format-identifier probability as a proxy for format uncertainty, including whether this proxy works beyond the specific “(A)” choice format?

**Answer:** Only partially. The paper gives a plausible formal decomposition of multiple-choice predictive probability into answer uncertainty conditioned on a response format and format uncertainty, and it provides some indirect empirical support via comparisons between pre-trained/aligned models, zero-shot/few-shot prompting, and synthetic alignment variants. However, the validation of the proxy for format uncertainty is limited: the main proxy is the probability of the format identifier “(” in the “(A)” format, and the paper does not sufficiently establish that this single-token probability is a reliable general measure of format uncertainty across alternative answer formats. The paper does compare “A” and “(A)” formats, but the format-identifier analysis appears specific to the “(A)” setting rather than a systematic validation over diverse identifiers, multi-token formats, natural-language answer formats, or prompt templates. As a result, the decomposition is useful and suggestive, but the central causal interpretation—that alignment separately alters answer and format uncertainty—is not fully validated by the evidence provided.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: Section 4.1 formalizes answer uncertainty and format uncertainty and decomposes predictive probability into an answer term conditioned on format and a format-probability term.
- paper: The paper uses the probability of the format identifier for the “(A)” choice format—specifically the identifier token “(”—as the operational measure of format uncertainty.
- paper: Section 3 evaluates both “A” and “(A)” choice formats, and Figure 4 is described as separating format preference from choice-letter probabilities for the “(A)” format.
- paper: Section 4.3 uses synthetic SFT/DPO variants, including format-only and choice-only alignment schemes, and reports that format-only alignment preserves calibration while choice/mixed alignment induces overconfidence, which indirectly supports the answer-vs-format distinction.
- paper: The paper itself relies on Assumption 4.1 that once format uncertainty is eliminated toward the MCQ format, the pre-trained model’s answer uncertainty is well-calibrated; this is an assumption rather than a fully demonstrated result.
- inference: The evidence supports the decomposition as a useful analytical lens, but the specific proxy is under-validated because it is tied to a convenient single-token format marker and is not shown to generalize to other common formats such as “A”, “Answer: A”, full option text, JSON-like outputs, or conversational responses.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall / ICLR format (pp. 1–8):**
  - The submission generally follows the ICLR single-column visual style with appropriate header, page numbers, section numbering, and equation numbering.
  - Text is readable, but pages are quite dense; several pages have little whitespace around figures and long paragraphs.
  - No tables are visible in the provided pages.

- **Figures legibility:**
  - **p. 1, Fig. 1:** The two plots are very small; axis labels, legends, and tick labels are difficult to read. The figure is placed in a cramped bottom-right area with text wrapping nearby, which hurts inspection.
  - **p. 3, Fig. 2:** The prompt diagram is visually useful but too small; many annotations and colored labels are hard to read without zooming.
  - **p. 4, Fig. 3:** Generally legible, though the legend is dense and small.
  - **p. 4, Fig. 4:** Multi-panel plot is crowded; subplot labels, legends, markers, and tick labels are borderline illegible at page scale.
  - **p. 6, Fig. 5:** Four small subplots are readable only with zoom; legends and tick labels are small.
  - **p. 7, Fig. 6:** Simple example box is mostly legible, but the text inside is small.
  - **p. 7, Fig. 7:** Dense multi-panel plot; legends and line labels are very small and difficult to distinguish visually.

- **Captions:**
  - Captions are generally informative and connected to the visual content.
  - **Fig. 1 caption (p. 1)** clearly states the diagram/histogram content and dataset.
  - **Fig. 2 caption (p. 3)** is concise and connected, but the figure itself contains too much tiny embedded text.
  - **Figs. 3–7 captions (pp. 4, 6–7)** describe the plotted results adequately, though some captions could mention the key visual takeaway to reduce reliance on tiny legends.

- **Layout / formatting issues:**
  - **p. 1:** The figure placement feels awkward and compressed; the main text wraps around Fig. 1, reducing readability.
  - **pp. 5–7:** Large blocks of body text, section headings, and assumptions appear in bright blue. If this is hyperlink coloring, it is over-applied and visually distracting; it makes ordinary prose look like links or emphasized text.
  - **p. 4:** Fig. 4 occupies a large area but still contains too many panels/legends for comfortable inspection.
  - **pp. 6–7:** Figures are squeezed between dense text blocks; more vertical spacing or larger figure sizing would improve readability.
  - Bullet list on **p. 7** is clear and well formatted.

- **Typography / equations:**
  - Equations are generally well centered, numbered, and readable.
  - **p. 5:** Equation with underbraces is visually understandable but somewhat small; underbrace labels may be hard to read at normal scale.
  - Inline math is frequent and dense but typographically consistent.
  - Footnote on **p. 5** is readable, though it adds to page density.

- **Ease of visual inspection as an ICLR submission:**
  - The paper is mostly easy to inspect structurally, with clear section hierarchy and standard formatting.
  - Main visual weakness is **figure readability**: many plots have tiny legends, axes, and embedded text.
  - The extensive **blue text coloring** is the most noticeable formatting distraction and should be toned down unless intentionally required for hyperlinks.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

### Q2

**Question:** Please inspect the remaining PDF pages, especially the appendices and any pages containing Tables 2–3 or full result tables, for readability/organization, table legibility, caption quality, and any formatting issues that affect ease of verification.

**Answer:** The appendix presentation is broadly organized and useful for verification, but the full-result tables are dense enough to create a nontrivial readability burden. Tables 2–3 appear to be more manageable than the larger full-result tables: they report targeted quantities, such as synthetic-task performance/calibration and learned task temperatures, and their captions are sufficiently informative for locating the relevant experiment. However, the later appendix result tables pack many datasets, model variants, settings, and metrics into compact table layouts. This makes them hard to inspect at normal reading scale and forces the reader to cross-reference abbreviations and experimental settings from the main text. The appendices are logically divided into prompts, experimental details, robustness/sensitivity analyses, synthetic-task results, calibration tables, and derivations, which is a presentation strength. The main weakness is that verification of numeric claims requires navigating visually crowded tables with small text and many abbreviated columns, rather than being able to quickly audit the results from self-contained, highly legible tables.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The appendix map indicates substantial supporting material: prompt examples, detailed experimental setups, full calibration results, prompt sensitivity analyses, dialog-wrapper experiments, ICL-mismatch experiments, synthetic-task results, full post-hoc calibration tables, and the derivation of the answer/format decomposition.
- paper: Table 2 is used for the synthetic MCQ alignment results, including the reported DPO-Format synthetic-task accuracy and MMLU calibration analysis; Table 3 reports task-specific learned temperatures for the proposed post-hoc method.
- paper: The paper relies on many repeated settings—zero-shot versus five-shot, choice formats such as “A” and “(A),” multiple datasets, multiple model families, and several calibration metrics—which increases the density of the appendix result tables.
- inference: Because the appendix tables aggregate many task/model/metric combinations, they support reproducibility but are less easy to verify visually. The captions and appendix organization help, but the compact full-table formatting is a presentation weakness for readers checking exact numerical claims.

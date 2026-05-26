# Q&A Trajectory

## Contribution

### Q1

**Question:** How novel are the two main proposed changes in R-EDL—treating the Dirichlet prior weight/lambda as tunable and removing the variance-minimizing term—relative to prior EDL, prior networks, and other Dirichlet-based uncertainty methods? Are these changes known or substantially new?

**Answer:** The two changes appear only moderately novel. Within the narrow Sensoy-style EDL formulation, R-EDL makes a useful and fairly clear contribution by identifying that the usual setting alpha=e+1 corresponds to a fixed prior weight W=C, replacing it with alpha=e+lambda, and by explicitly dropping the variance-minimizing part of the original EDL MSE Bayes-risk objective. However, these ideas are not substantially new in the broader Dirichlet-uncertainty literature: subjective logic already treats the prior weight as a given/design quantity rather than a mathematical necessity, and prior-network/Dirichlet-target methods commonly choose Dirichlet concentration or precision parameters as training design choices. Likewise, training a Dirichlet predictor without the particular EDL MSE variance term is already common in prior networks and other Dirichlet methods using KL, NLL, or target-concentration objectives. Thus the contribution is best viewed as an incremental but useful reinterpretation and simplification of EDL, plus empirical validation, rather than a fundamentally new Dirichlet uncertainty mechanism.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper's own formulation says subjective logic gives a bijection between opinions and Dirichlet PDFs when base rate and prior weight W are given, so W is not derived uniquely by the theory. R-EDL then generalizes traditional EDL from alpha_x=e_x+1 to alpha_x=e_x+lambda, where lambda=W/C is treated as a hyperparameter.
- paper: The paper decomposes the traditional EDL objective into squared error on the Dirichlet expectation plus a variance-minimized regularization term, and R-EDL removes that term by directly optimizing the projected probability/expectation. The ablations then test lambda=1 and reintroducing L_var, showing modest performance drops relative to full R-EDL.
- paper: The related-work positioning claims R-EDL is the first method to relax these “nonessential settings” of traditional EDL while adhering to subjective logic, but the paper also lists prior networks, posterior networks, KL-PN/RKL-PN, and other Dirichlet-based methods as related baselines.
- retrieval: No external retrieval results were provided in the tool observations for this QA item, so the prior-work judgment is based on the paper's related-work map plus reviewer knowledge rather than verified retrieved excerpts.
- inference: Relative to Prior Networks and related Dirichlet methods, the idea of choosing Dirichlet concentration/precision parameters is already established; relative to EDL specifically, making lambda explicit and linking it to over-confidence is a more focused contribution. Similarly, omitting the EDL variance term is not broadly novel because many Dirichlet predictors do not use that objective, but the paper's diagnosis of that term inside traditional EDL is a useful clarification.

### Q2

**Question:** How broad and significant is the empirical impact of R-EDL across the reported settings? Are the gains over EDL and other Dirichlet/single-forward-pass uncertainty baselines large and consistent enough to support a strong contribution claim, or are they mostly modest/narrow?

**Answer:** R-EDL’s empirical impact is fairly broad in scope but mostly moderate in magnitude. The paper evaluates it across classical image classification/OOD detection, few-shot OOD detection, noisy CIFAR-10, and video open-set recognition, which gives the contribution reasonable empirical breadth. Reported results generally favor R-EDL over traditional EDL and several Dirichlet or single-forward-pass uncertainty baselines, supporting the claim that the relaxation is useful. However, the closest controlled comparisons and ablations suggest the gains are often incremental rather than large: e.g., in the ablation setting, CIFAR-10 to SVHN OOD AUPR improves from 83.24 with lambda fixed to 1 and 84.04 with the variance term restored to 85.00 for full R-EDL; in 10-way 5-shot mini-ImageNet to CUB, full R-EDL reaches 83.37 versus 82.89 and 82.25 for the ablated variants. Thus, the empirical evidence supports R-EDL as a useful and consistently competitive refinement of EDL, but the margin over close EDL variants appears modest. This makes the contribution solid, especially because it is simple and broadly tested, but not an overwhelmingly large empirical advance.

**Impact:** strength, C2, confidence=medium

**Evidence:**
- paper: The paper reports experiments across multiple settings: classical MNIST/CIFAR-10 confidence and OOD detection, few-shot mini-ImageNet with CUB as OOD, noisy CIFAR-10, and video open-set action recognition with UCF-101 as ID and HMDB-51 or MiT-v2 as OOD.
- paper: In the classical setting, R-EDL reports 99.33% MNIST accuracy and 90.09% CIFAR-10 accuracy, and the paper states that it improves CIFAR-10 to SVHN OOD AUPR over EDL and I-EDL when using maximum probability.
- paper: In few-shot experiments, R-EDL reports strong AUPR scores, including 83.65 MP OOD AUPR for 5-way 5-shot mini-ImageNet to CUB.
- paper: Ablation results show modest but consistent gains from the two proposed relaxations: CIFAR-10 to SVHN OOD AUPR is 85.00 for full R-EDL, compared with 83.24 when lambda is fixed to 1 and 84.04 when the variance-minimized term is reintroduced; 10-way 5-shot mini-ImageNet to CUB OOD AUPR is 83.37 for full R-EDL, compared with 82.89 and 82.25 for the two ablations.
- paper: Appendix video results report R-EDL scores of 78.73 open maF1 and 77.94 open-set AUC for UCF-101 to HMDB-51, and 70.85 open maF1 and 82.26 open-set AUC for UCF-101 to MiT-v2, outperforming the listed video baselines according to the paper summary.
- inference: Because the evaluation spans several modalities and distribution-shift regimes, the empirical scope is broad. But because the clearest controlled gains over close EDL variants are often around one to two AUPR points, the contribution is better characterized as a consistent, useful refinement than as a dramatic empirical leap.

### Q3

**Question:** Does the paper provide a compelling conceptual/theoretical contribution in its reinterpretation of EDL through subjective logic—especially the claim that fixed prior weight and the variance term are “nonessential”—or is the contribution mainly an engineering/empirical simplification?

**Answer:** The contribution is best viewed as a useful engineering and empirical simplification with some conceptual clarification, rather than a deep new theoretical reinterpretation of EDL. The paper’s strongest conceptual point is that, under subjective logic, the Dirichlet prior weight need not be fixed to the number of classes: given a base rate and prior weight, subjective opinions map to Dirichlet parameters, so treating the prior weight as a tunable hyperparameter is consistent with the framework. The paper also algebraically identifies the traditional EDL loss as containing a variance-minimizing term and argues that this term can push the Dirichlet toward over-confident, Dirac-delta-like behavior. However, these points mostly relax implementation choices in prior EDL rather than introduce a substantially new theoretical model of uncertainty. The paper itself reinforces this interpretation by leaving the optimal prior-weight mechanism for future work and by describing its objective—optimizing the Dirichlet expectation/projected probability—as somewhat coarse. The empirical ablations support the practical usefulness of removing/flexibilizing these settings, but the gains from the individual relaxations appear moderate, which makes the contribution more compelling as a simplification and performance improvement than as a major conceptual advance.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: Section 2 states the subjective-logic relationship: given base rate and prior weight W, there is a bijection between multinomial opinions and Dirichlet PDFs, with concentration parameter alpha expressed using belief, uncertainty, base rate, and W. This supports the paper’s claim that W is part of the subjective-logic parameterization rather than necessarily fixed to the class count.
- paper: Section 3.2 generalizes traditional EDL from alpha_x = e_x + 1 to alpha_x = e_x + lambda, where lambda = W/C is treated as a hyperparameter. This is a relaxation of a prior modeling choice rather than a wholly new uncertainty formalism.
- paper: The paper derives that the traditional EDL squared-error objective can be written as squared error on the Dirichlet expectation plus a variance-minimized regularization term, and then removes that variance term in the R-EDL loss. This provides an algebraic justification for the “nonessential” claim.
- paper: The ablation study reports that restoring lambda = 1 or reintroducing the variance term reduces performance relative to R-EDL, e.g. on CIFAR-10 to SVHN OOD AUPR, R-EDL reports 85.00 versus 83.24 for lambda = 1 and 84.04 with the variance term. This supports practical utility but suggests incremental rather than transformative gains.
- paper: The conclusion explicitly leaves “the mechanism dictating the optimal prior weight value” for future work and says the current objective optimizes the expected value of the Dirichlet PDF in a “somewhat coarse” way. These limitations weaken the claim of a fully compelling theoretical contribution.
- retrieval: No external scholarly retrieval results were available in the provided tool observations, so the novelty assessment is based on the paper’s own positioning and reviewer judgment rather than independent prior-work verification.
- inference: Because the subjective-logic mapping is used mainly to justify relaxing hyperparameters and dropping a loss component, and because the paper validates these choices primarily through ablations and benchmark improvements, the contribution is more engineering/empirical than theoretical.

## Soundness

### Q1

**Question:** Does the paper rigorously justify the two central theoretical claims: (1) that setting alpha=e+lambda with lambda not equal to 1 remains a valid subjective-logic/Dirichlet opinion mapping, and (2) that the variance term in the traditional EDL loss indeed encourages over-confident or Dirac-delta-like Dirichlet distributions? Please summarize any derivations or caveats.

**Answer:** The paper gives a reasonably valid but not fully exhaustive theoretical justification for both claims. For claim (1), the justification is fairly sound: subjective logic permits a Dirichlet opinion mapping with an arbitrary positive prior weight W, and under a uniform base rate this yields alpha_k = e_k + W/C. Thus defining lambda = W/C gives alpha_k = e_k + lambda, so lambda need not equal 1 as long as it corresponds to a positive prior weight. The main caveat is that the paper justifies validity of the mapping, not an optimal choice of lambda; that remains empirical and is acknowledged as future work. For claim (2), the paper derives the traditional EDL expected squared-error loss as a squared error on the Dirichlet mean plus an additional Dirichlet variance term, and argues that minimizing this variance encourages concentration of the Dirichlet density, making it sharper and more Dirac-delta-like. This is directionally plausible because Dirichlet variance decreases as total concentration grows, especially when the mean is held fixed. However, the argument is less rigorous as a complete overconfidence proof: minimizing variance alone does not uniquely imply harmful overconfidence in all training regimes, and the paper’s claim depends on the interaction between fitting the label mean and increasing concentration. Therefore, the first theoretical claim is well grounded in subjective-logic parameterization, while the second is supported by derivation and intuition but is more qualitative and should be treated as a plausible mechanism rather than a fully formal theorem.

**Impact:** strength, C2, confidence=medium

**Evidence:**
- paper: The paper’s Subjective Logic section states that, given base rate and prior weight W, there is a bijection between multinomial opinions and Dirichlet PDFs, with concentration parameter alpha_X(x)=b_X(x)W/u_X+a_X(x)W. Under uniform base rate a_X(x)=1/C and defining evidence through belief/uncertainty, this supports alpha_k=e_k+W/C.
- paper: The R-EDL method section generalizes traditional EDL’s alpha_k=e_k+1 to alpha_k=e_k+lambda, identifying lambda=W/C and treating it as a hyperparameter rather than fixing W=C. This directly supports the claim that lambda different from 1 is compatible with subjective logic when interpreted as changing prior weight.
- paper: The paper decomposes the traditional EDL loss into an error term between the one-hot label and the Dirichlet expected/projected probability plus a variance-minimized regularization term. It claims this variance term drives the Dirichlet PDF toward a Dirac-delta-like distribution and may heighten overconfidence.
- paper: The conclusion/limitations acknowledge that the mechanism determining the optimal prior weight remains for future work and that directly optimizing only the Dirichlet expected value is relatively coarse, suggesting the theory does not fully settle all design choices.
- inference: The lambda mapping is mathematically justified if lambda>0, because Dirichlet concentration parameters must be positive and lambda corresponds to prior weight per class. But the paper’s theoretical argument does not itself establish which lambda yields best calibration or OOD behavior.
- inference: The variance-term argument is plausible because Dirichlet variance decreases with larger total concentration. When the loss also fits a one-hot target mean, reducing variance can encourage high concentration near a class vertex. Still, this is a mechanism-level argument rather than a formal proof that the traditional loss necessarily causes overconfidence under all conditions.

### Q2

**Question:** Are the experimental baselines and evaluation protocols strong and fair for the main claims? In particular, does the paper compare against current competitive uncertainty/OOD/calibration methods with matched architectures, training budgets, and tuning, and are there any notable missing baselines or protocol caveats?

**Answer:** The baseline suite is reasonably strong for the paper’s narrower claim that relaxing standard EDL settings improves over EDL-style Dirichlet uncertainty methods: it compares to EDL, I-EDL, prior-network variants, Posterior Network, DUQ, MC Dropout, and includes ablations restoring lambda=1 and the EDL variance term. This supports the internal methodological claim. However, it is less convincing for broad claims about competitive uncertainty estimation, OOD detection, and calibration. The main comparisons appear to omit several widely used modern OOD/scoring and calibration baselines that can often be run with matched backbones, such as ODIN, energy score, MaxLogit/MSP-style strong post-hoc scoring, Mahalanobis, ViM, ReAct/DICE/ASH-style activation/logit methods, and stronger ensemble or calibration baselines. Temperature scaling is only mentioned as additional calibration evidence rather than being central to the main protocol. The protocol also leaves caveats about fairness: the summary indicates lambda is selected by validation classification accuracy, but it is unclear whether all baselines receive comparable hyperparameter tuning for uncertainty/OOD metrics; matched architectures and training budgets are not clearly established from the provided experimental map; and the main tables emphasize AUPR rather than a fuller OOD/calibration suite such as AUROC/FPR95/ECE/Brier in the primary results. Overall, the experiments are fair enough for an EDL-family improvement claim, but not fully sufficient to establish state-of-the-art or broadly competitive uncertainty/OOD/calibration performance.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The experiments compare R-EDL against EDL, I-EDL, KL-PN, RKL-PN, Posterior Network, DUQ, and MC Dropout in classical image settings, and against OpenMax, MC Dropout, BNN SVI, RPL, and DEAR in video settings.
- paper: The paper includes targeted ablations: fixing lambda=1 to restore the original EDL prior-weight setting and reintroducing the variance-minimized regularization term, with corresponding drops in reported OOD AUPR.
- paper: The reported main metrics include classification accuracy and AUPR for confidence estimation/OOD detection using max probability and uncertainty mass; additional appendix metrics include AUROC, ECE, Brier score, entropy-based measures, and video open-set metrics.
- paper: For CIFAR-10, lambda is selected from a validation range based on validation classification accuracy; the provided map does not establish that all baselines were tuned comparably for OOD/calibration performance.
- inference: Because the paper’s main baseline set focuses on EDL/Dirichlet and selected uncertainty methods, missing common post-hoc OOD and calibration baselines limit the strength of broad claims about competitive uncertainty/OOD/calibration performance, even if the EDL-specific comparisons are meaningful.

### Q3

**Question:** Do the ablation studies and parameter analyses sufficiently isolate the effects of the two proposed relaxations? Please assess whether the reported gains are large and consistent enough, whether interactions between lambda selection and removing the variance term are tested, and whether sensitivity to lambda undermines or supports the claims.

**Answer:** The ablations only partially isolate the two relaxations. The paper does include targeted variants: one restores the original prior-weight setting by fixing lambda=1, and another reintroduces the variance-minimized regularization term L_var. These comparisons support the claim directionally: reported OOD AUPR drops from R-EDL's 85.00 to 83.24 with lambda=1 and to 84.04 with L_var on CIFAR-10 vs SVHN, and from 83.37 to 82.89 and 82.25 respectively in the 10-way 5-shot mini-ImageNet to CUB setting. However, the gains are modest—often below 1-2 AUPR points—and the evidence provided does not appear to include error bars, significance tests, or repeated-run variability, so it is hard to judge whether these changes are robust rather than noise or tuning effects.

The more important limitation is that the ablation is not a full factorial analysis. The paper tests lambda=1 and adding L_var separately, and notes that restoring both original settings recovers traditional EDL, but it does not appear to test the interaction between lambda selection and L_var removal. In particular, it does not show whether the best lambda changes when L_var is present, whether L_var is still harmful under an optimally tuned lambda, or whether the apparent benefit of removing L_var depends on choosing lambda=0.1. The parameter analysis varies lambda from 0.01 to 1.5 and evaluates CIFAR-10 accuracy and CIFAR-100 OOD AUPR, which supports the claim that lambda matters, but also raises sensitivity concerns because the method's gains may depend on validation-selected lambda. The authors themselves indicate that the mechanism for choosing the optimal prior weight remains future work.

Overall, the ablations are useful and directionally consistent, especially for OOD detection, but they are not strong enough to fully isolate the causal effects of the two relaxations. This is a soundness weakness rather than a fatal flaw: the experiments support the proposed design choices, but the lack of interaction testing and statistical robustness weakens the strength of the methodological conclusion.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: Section 5.5 states that the ablation assesses the two relaxations by retaining the original lambda=1 setting and by reintroducing the deprecated variance-minimized regularization term L_var; it also states that restoring both original settings reverts R-EDL to traditional EDL.
- paper: Table 3 reports directional drops in OOD performance: on CIFAR-10 vs SVHN, R-EDL obtains 85.00 AUPR compared with 83.24 for lambda=1 and 84.04 with L_var; on 10-way 5-shot mini-ImageNet to CUB, R-EDL obtains 83.37 compared with 82.89 and 82.25.
- paper: Figure 1(b) is described as a parameter analysis varying lambda from 0.01 to 1.5 and evaluating CIFAR-10 classification accuracy and CIFAR-100 OOD AUPR. The paper also reports selecting lambda=0.1 for CIFAR-10 from a validation grid based on classification accuracy.
- paper: The conclusion lists the mechanism for determining the optimal prior-weight value as future work, indicating that lambda selection remains incompletely understood.
- inference: Because the reported ablations vary lambda and L_var separately but do not show a grid over lambda with and without L_var, they do not fully test whether the two relaxations interact. The small reported gains and lack of apparent uncertainty estimates further limit causal strength.

### Q4

**Question:** Does the paper report sufficient statistical evidence and metric coverage to support its empirical conclusions, e.g., repeated runs, standard deviations/confidence intervals, significance tests, validation/test separation, and calibration/OOD metrics beyond AUPR? Please summarize any shortcomings that affect soundness.

**Answer:** The paper provides broad empirical coverage across datasets and includes useful ablations, but its statistical support appears limited. The main experimental claims are mostly backed by point estimates in accuracy and AUPR tables, plus ablations over the two proposed relaxations. I did not find evidence in the provided paper map that the main results include repeated-run averages, standard deviations, confidence intervals, or statistical significance tests. This is a soundness concern because many reported improvements are modest, e.g. ablation differences of roughly 1--2 AUPR points, so it is hard to judge whether the gains are robust to initialization, data splits, or few-shot episode sampling.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The main experiments report classification accuracy and AUPR for confidence estimation and OOD detection, using max probability and uncertainty mass as scores for Dirichlet-based methods.
- paper: The ablation section compares R-EDL against variants with lambda fixed to 1 and with the variance-minimized term restored; reported improvements include CIFAR-10 to SVHN OOD AUPR of 85.00 for R-EDL versus 83.24 and 84.04 for the variants, and mini-ImageNet to CUB OOD AUPR of 83.37 versus 82.89 and 82.25.
- paper: The paper reports that lambda is selected for the CIFAR-10 setting from a validation range based on validation classification accuracy, which is a positive indication of some validation/test separation, but the summary does not indicate equally explicit validation procedures for all settings or for OOD-specific hyperparameter selection.
- paper: Additional appendix material includes broader uncertainty/calibration metrics such as AUROC, expected calibration error, Brier score, differential entropy, mutual information, and expected entropy, and video open-set experiments report open maF1 and open-set AUC.
- inference: Metric coverage is therefore better than the main-text AUPR-only impression, but the central empirical narrative appears to rely heavily on AUPR point estimates. Calibration metrics and alternative OOD metrics seem less central, and the absence of reported uncertainty over runs weakens confidence in small margins.
- inference: The main soundness shortcoming is not that no empirical support is provided, but that the paper does not appear to quantify experimental variability or statistical significance. This limits the strength of conclusions about reliable superiority over EDL, I-EDL, and other uncertainty baselines.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall / ICLR visual inspectability (pp. 1–8):** The paper is generally easy to visually inspect as an ICLR-style submission: clean single-column layout, consistent headers/footers, readable body text, and standard section/equation formatting.

- **Figures:** No actual figures are visible in the provided pages. Page 8 references “Fig. 1(a),” but the figure is not present in the shown pages, so figure legibility/caption quality cannot be assessed from this excerpt.

- **Tables legibility (p. 8):**
  - **Table 1** is mostly legible, but it is dense with many columns, multiple dataset sections, small numeric text, and many vertical dividers. It may be hard to read at reduced zoom or in print.
  - **Table 2** is even more compact, with many multi-column headers and tightly packed numeric entries; legibility is marginal compared with the rest of the paper.
  - Boldface best results are visible and helpful, but the density makes comparisons visually demanding.

- **Captions (p. 8):**
  - Table captions are informative and connected to the table content.
  - Table 1 caption explains datasets, averaging, model backbones, ID/OOD notation, and metric abbreviations, which is helpful.
  - Table 2 caption is concise and clear, though some abbreviations/episode settings are explained in surrounding text rather than the caption itself.

- **Equations (pp. 2–6):**
  - Equations are generally well typeset and readable.
  - Some long equations, especially Eq. 2 on p. 2 and Eq. 13 on p. 6, are visually dense but remain within margins.
  - Equation numbering and cross-references are clear.

- **Typography / formatting:**
  - Body text is readable and consistent throughout.
  - Colored hyperlinks/cross-references in blue/red are functional but visually prominent; the frequent red equation/section references can be slightly distracting.
  - Page 1 title line break after “Ev-” is acceptable but visually a bit awkward.
  - Footnotes on pp. 1–2 are small but legible.

- **Layout density:**
  - Pages 2–7 are text-heavy but still well structured with section headings and displayed equations.
  - Page 8 is the main visual bottleneck: two large tables plus surrounding text create a crowded page. Consider splitting Table 2 or moving supplementary details to appendix for easier inspection.

- **Summary:** Presentation quality is generally strong and conforms well to ICLR expectations. The main readability concern is the high density and small font size of the experimental tables on page 8; figures cannot be evaluated from the provided pages.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

### Q2

**Question:** Please inspect the remaining PDF pages beyond page 8, especially the pages containing Figure 1, ablation/parameter-analysis tables, appendices, and any additional experimental tables. Are these figures/tables/captions legible and well explained, and are there any formatting or organization issues that affect readability?

**Answer:** The remaining inspected PDF pages are generally readable, but there are minor presentation issues. On page 9, Figure 1 and Table 3 are legible and have informative captions: Figure 1’s caption explains the noisy-setting trend plot and the lambda parameter analysis, and Table 3’s caption clearly identifies the two ablated relaxations. However, Figure 1 is somewhat visually dense: the parameter-analysis subplot includes many numeric labels across two curves, and the noisy-setting subplot/caption gives only high-level context, so the reader still needs nearby prose to fully interpret the datasets/metrics. Table 3 is readable but compact, with multi-level headers, arrows, abbreviations such as “Cls Conf” and “OOD Detect,” and dense ± statistics; this is acceptable but not maximally easy to scan. Pages 10–11 are references and are formatted normally, though there are minor typesetting/spacing artifacts in the extracted text such as missing spaces around conference names. The provided page-level evidence does not include the later appendix pages, so my inspection of appendix tables is necessarily incomplete; based on the paper map, the appendices contain many additional derivations and experimental tables, and the organization appears conventional, but the visual legibility of those later appendix tables cannot be fully verified from the available PDF text. Overall, the presentation is mostly clear, with only minor readability issues rather than serious formatting problems.

**Impact:** weakness, C1, confidence=medium

**Evidence:**
- paper: PDF page 9 contains Figure 1 with two subfigures: “(a) Performance in noisy setting” and “(b) Parameter analysis,” with axes for AUPR score of OOD detection, classification accuracy, and hyper-parameter λ. The caption explains that Figure 1(a) reports average classification/OOD performance across Gaussian noise levels and Figure 1(b) evaluates λ by CIFAR-10 accuracy and CIFAR-100 OOD AUPR.
- paper: PDF page 9 contains Table 3, captioned as an ablation study for treating λ as a hyperparameter and deprecating Lvar. The table has grouped columns for classical and few-shot settings and reports EDL, I-EDL, R-EDL w/ λ=1, R-EDL w/ Lvar, and R-EDL results with confidence intervals.
- paper: PDF pages 10–11 are references and appear conventionally organized, but the extracted text shows minor spacing/formatting artifacts such as “InProceedings” and uneven spacing around some venue names.
- inference: Figure 1 and Table 3 are legible and sufficiently captioned, but their density, abbreviations, and compact multi-level formatting make them slightly harder to inspect quickly. The absence of available page-level text for later appendices limits confidence about appendix table legibility.

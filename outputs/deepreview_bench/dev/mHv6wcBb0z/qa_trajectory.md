# Q&A Trajectory

## Contribution

### Q1

**Question:** Is the paper’s claimed “model collapse” phenomenon in DCCA-based methods and its diagnosis as spurious model-induced correlation actually novel relative to prior work on DCCA/CCA regularization, representation collapse, or degenerate correlation objectives?

**Answer:** Only partially. The paper appears to offer a useful empirical framing for DCCA-specific training-time degradation: downstream performance can initially improve and then collapse, while transformed unrelated/noise data become increasingly correlated. That specific diagnostic—“model-induced correlation” in DCCA/DGCCA representations—may be a relatively fresh presentation. However, the broader phenomenon is not clearly novel: CCA/DCCA objectives are well known to require covariance/ridge regularization to avoid ill-conditioned or degenerate correlation maximization, and representation-collapse/degenerate-objective issues are widely discussed in related representation-learning settings. The paper’s related-work claim that DCCA-based model collapse “has not been explored and addressed” is therefore too strong unless supported by a much more careful comparison to prior CCA/DCCA regularization and collapse/degeneracy literature. Because no external retrieval results were available in this session, I would not conclude that the paper is definitively non-novel; rather, I would judge the novelty claim as under-substantiated and likely overstated.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper claims that DCCA-based methods can suffer drastic downstream performance drops as training proceeds and names this “model collapse.” It further claims that collapse arises because powerful neural transformations create “model correlation” rather than true view correlation.
- paper: The related-work section reportedly states that the model-collapse issue of DCCA-based methods has not been explored and addressed, and that using noise regularization for DCCA-based methods to prevent collapse has not been studied.
- paper: The paper’s own empirical diagnosis is that transformed unrelated data exhibit increasing correlation in collapsed DCCA-based models, and it proposes noise regularization to penalize changes in correlation between real data and Gaussian noise after transformation.
- paper: The appendix also reports that standard ridge regularization for DCCA does not prevent collapse in their CUB experiment, suggesting the authors are aware of at least one existing regularization baseline but do not fully position against the broader CCA/DCCA degeneracy literature.
- retrieval: No external scholarly retrieval results were provided in the tool observations, so I cannot verify the full prior-work landscape directly here. This lowers confidence in any definitive novelty judgment.
- inference: As reviewer judgment, the specific “spurious model-induced correlation” diagnostic in DCCA may be a contribution, but the broad idea that correlation-maximization objectives can become ill-conditioned, degenerate, or require regularization is established enough that the paper should not claim the phenomenon is wholly unexplored without stronger prior-work analysis.

### Q2

**Question:** How technically novel is the proposed NR-DCCA method itself: is penalizing the change in correlation between real data and Gaussian noise after transformation meaningfully different from existing noise regularization, denoising/contractive regularization, orthogonality/full-rank constraints, or covariance/ridge regularization used in DCCA/CCA?

**Answer:** NR-DCCA has a somewhat distinctive formulation, but the technical novelty appears moderate rather than strong. The paper's specific penalty—matching Corr(f_k(X_k), f_k(A_k)) to Corr(X_k, A_k), where A_k is Gaussian noise—is not simply the usual DCCA covariance/ridge stabilization term, nor a standard orthogonality constraint, because it regularizes how a neural view encoder changes correlations between real samples and independent noise. It is also framed differently from denoising/contractive regularization, which usually penalizes reconstruction sensitivity or local Jacobian behavior rather than preservation of data-noise correlation. However, the contribution is weakened by the fact that the proposed “full-rank” neural-network property is essentially defined through this new penalty, and the paper does not convincingly establish that this is a fundamentally new regularization principle rather than a variant of existing noise/sensitivity/rank-preservation regularization. The paper itself acknowledges that further investigation is needed into what is actually regularized by the noise and how the idea differs from orthogonalization and weight decay. Thus, the method is meaningfully different at the level of objective design, but its deeper technical novelty over existing regularization families is only partially substantiated.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: Section 4 defines NR-DCCA as generating i.i.d. Gaussian white noise with the same shape as each view and adding a loss term that penalizes the absolute difference between the correlation of transformed real data and transformed noise and the original correlation between real data and noise.
- paper: The paper's theory argues that, for square full-rank linear CCA transformations, correlation between data and Gaussian noise is invariant before and after transformation, and conversely that the invariance condition implies full rank in the linear CCA setting.
- paper: For neural networks, the paper defines a network as “full-rank” when the proposed noise-regularization term is zero, which makes the neural full-rank notion partly definitional rather than an independently established algebraic property.
- paper: The appendix reports an ablation in which varying DCCA ridge regularization on CUB does not prevent collapse, suggesting the proposed penalty behaves differently from simple covariance/ridge regularization in their experiments.
- paper: The conclusion/reproducibility discussion lists as future work further investigation of the proposed neural-network “full-rank” definition, differences from orthogonalization and weight decay, and what quantities are actually regularized by the noise.
- retrieval: No usable external scholarly retrieval results were available in this QA context, so the assessment of novelty relative to the broader literature is based primarily on the paper's positioning and reviewer judgment rather than independently verified prior-work comparisons.
- inference: The penalty is formally distinct from standard DCCA ridge/covariance regularization and from direct orthogonality constraints, because it constrains correlations with injected noise after the encoder. But because it is still a noise-based regularizer and the paper does not rigorously distinguish it from denoising, contractive, orthogonalization, or weight-decay mechanisms, the technical novelty is best viewed as incremental-to-moderate rather than clearly high.

### Q3

**Question:** How broad and impactful is the contribution likely to be: does NR-DCCA address an important practical failure mode across multi-view/self-supervised representation learning, or is its impact mostly limited to DCCA/DGCCA settings and the specific benchmarks studied?

**Answer:** NR-DCCA appears to address a meaningful and practically relevant failure mode, but the demonstrated contribution is mostly limited to DCCA/DGCCA-style correlation-maximization methods rather than broad multi-view or self-supervised representation learning. The paper's core problem framing, theory, and algorithm are all tied to DCCA-based model collapse and to enforcing a CCA-like full-rank property by preserving correlations between real data and injected Gaussian noise. The method is shown to extend to DGCCA, which broadens the contribution within the CCA family, but the paper does not demonstrate effectiveness for major non-CCA multi-view/self-supervised paradigms such as contrastive learning or generative SSL; instead, it explicitly lists such extensions as future work. Thus, the contribution is potentially impactful for users of DCCA/DGCCA, especially because collapse can make DCCA worse than CCA or feature concatenation, but the current evidence does not justify a claim of broad impact across self-supervised representation learning.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: The paper frames the central failure mode as one of “DCCA-based methods,” describing drastic downstream performance drops during training and arguing that NR-DCCA prevents this model collapse by constraining neural networks to have a CCA-like full-rank property.
- paper: The proposed regularizer is specifically defined around the DCCA setting: it generates Gaussian white noise for each view and penalizes the change in correlation between real data and noise before versus after each view-specific neural transformation. The theoretical motivation is based on full-rank square linear transformations in CCA.
- paper: The paper reports empirical gains on synthetic data and on PolyMnist, CUB, and Caltech101, with baselines centered on CCA/DCCA variants such as CCA, PRCCA, KCCA, DCCA, DGCCA, DCCAE/DGCCAE, DCCA PRIVATE/DGCCA PRIVATE, plus MVTCAE.
- paper: The paper claims the noise regularization generalizes to DGCCA and the appendix reports NR-DGCCA experiments, but broader paradigms are not evaluated.
- paper: The conclusion lists exploring noise regularization in contrastive learning and generative models as future work, which indicates that broad applicability to self-supervised learning remains unproven in the submission.
- retrieval: No external retrieved papers were provided. The available tool observation reports no matches for a search targeting “contrastive learning generative models DCCA-based methods collapse,” so the assessment relies primarily on the paper’s own scope and evidence.
- inference: Because the mechanism and theory depend on CCA/DCCA correlation objectives, and because experiments are confined to DCCA/DGCCA-style methods and a small set of benchmarks, the likely contribution breadth is narrower than the broad phrase “multi-view/self-supervised representation learning” might imply.

## Soundness

### Q1

**Question:** Are the theoretical claims connecting the proposed noise regularization to “full-rank” transformations technically valid under clearly stated assumptions? In particular, do Propositions 3–4 require square/invertible linear maps, specific definitions of correlation, or Gaussian/isotropic noise, and is the extension from these linear results to neural networks justified rather than merely definitional?

**Answer:** I cannot make a fully evidenced judgment from the available excerpt because the exact proposition text was not retrieved: a search for “Proposition 3 full-rank correlation noise” returned no matches. Based on the paper map, however, the theory appears to support only a narrow linear claim: Propositions 3–4 are stated for square CCA transformations, with Proposition 3 asserting invariance of data-noise correlation under full-rank square linear transformations and Proposition 4 asserting the converse. This makes the assumptions central: the result seems to depend on square/invertible linear maps and on the paper’s particular correlation measure between transformed data and generated noise. The paper also reportedly uses i.i.d. Gaussian white noise, but from the available evidence it is unclear whether Gaussianity is mathematically necessary or whether isotropy/zero correlation would suffice. The extension to neural networks is weaker: the paper defines a neural network as “full-rank” when the noise-regularization term is zero, rather than proving that the network has a genuine rank/invertibility/non-collapse property analogous to the linear case. The conclusion/reproducibility discussion itself reportedly lists further investigation of this “full-rank” neural-network definition as future work. Thus, as a soundness matter, the theoretical connection is only partially justified: the linear propositions may be valid under restrictive assumptions, but the broader claim that noise regularization enforces full-rank neural transformations and thereby prevents collapse is not established by a clear theorem; it is largely definitional plus empirical.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: Paper map states that NR-DCCA generates i.i.d. Gaussian white noise with the same shape as each input view and penalizes the absolute difference between Corr(f_k(X_k), f_k(A_k)) and Corr(X_k, A_k).
- paper: Paper map states that Proposition 3 claims correlation between data and noise is invariant for full-rank square linear CCA transformations, and Proposition 4 claims that if this invariance holds for a square CCA transformation, the transformation must be full-rank.
- paper: Paper map states that Definition 2 defines a neural network f_k as “full-rank” when the NR loss term zeta_k equals 0.
- paper: Paper map reports a stated limitation/future work: further investigating the proposed “full-rank” neural-network definition and what/how neural networks are regularized through noise.
- retrieval: A search for the exact phrase “Proposition 3 full-rank correlation noise” returned no matches, so the exact proof details and definitions were not verified directly from the proposition text.
- inference: If the propositions are limited to square linear transformations, they do not by themselves prove analogous rank, injectivity, or anti-collapse behavior for nonlinear neural networks. Defining zero regularization loss as “full-rank” is not equivalent to proving a conventional full-rank property.

### Q2

**Question:** Do the experiments include sufficiently strong and properly tuned baselines, especially standard anti-collapse or regularization alternatives for DCCA such as early stopping, dropout, weight decay, orthogonality/whitening constraints, reconstruction losses, or covariance/rank regularizers, and are baseline hyperparameters tuned comparably to NR-DCCA?

**Answer:** No. The experimental comparison includes several relevant CCA/DCCA-family baselines, but the anti-collapse baseline coverage and tuning evidence appear insufficient. The paper compares against CONCAT, CCA/PRCCA/KCCA, DCCA/DGCCA, DCCAE/DGCCAE, DCCA PRIVATE/DGCCA PRIVATE, and MVTCAE, and it includes one appendix ablation varying DCCA ridge regularization on CUB. However, the provided paper evidence does not show systematic comparisons to common anti-collapse or regularization alternatives such as early stopping, dropout, weight decay, orthogonality/whitening constraints, covariance/rank regularizers, or comparably tuned reconstruction-loss variants as explicit anti-collapse controls. The paper itself lists future investigation of differences from orthogonalization and weight decay, suggesting those alternatives were not experimentally resolved. It does tune the proposed NR-DCCA regularization weight alpha, but the evidence for comparable baseline hyperparameter tuning is limited mainly to ridge regularization for DCCA, not a broad or matched tuning protocol across regularized baselines. This matters for soundness because the main empirical claim is that noise regularization prevents DCCA collapse; without strong, tuned anti-collapse baselines, it is hard to determine whether the gains are specific to the proposed noise regularizer or would also be achieved by standard regularization, stopping, whitening/rank constraints, or reconstruction-based stabilizers.

**Impact:** weakness, C3, confidence=medium

**Evidence:**
- paper: The experiments include baselines such as CONCAT, CCA, PRCCA, KCCA, DCCA, DGCCA, DCCAE/DGCCAE, DCCA PRIVATE/DGCCA PRIVATE, and MVTCAE.
- paper: The appendix includes an ablation varying the ridge regularization parameter r for DCCA on CUB and reports that ridge regularization does not prevent collapse.
- paper: The appendix also varies the NR-DCCA regularization weight alpha on CUB, indicating direct tuning/sensitivity analysis for the proposed method.
- paper: The conclusion/reproducibility discussion lists future work on investigating differences from orthogonalization and weight decay, implying those standard alternatives were not fully compared in the reported experiments.
- inference: Because only ridge regularization is identified as a tested anti-collapse regularizer, and because no comparable tuning evidence is provided for early stopping, dropout, weight decay, orthogonality/whitening constraints, covariance/rank regularizers, or explicit anti-collapse reconstruction-loss variants, the baseline suite is not strong enough to fully isolate the proposed method's contribution.

### Q3

**Question:** Are the reported experimental results statistically reliable and complete enough to support the stability/collapse-prevention claims? Specifically, do they report variance/error bars or significance across seeds/folds, evaluate final-epoch versus best-epoch performance, and use metrics that directly demonstrate collapse prevention rather than only downstream task performance?

**Answer:** The evidence is only partially complete and is not statistically strong enough to fully support the stability/collapse-prevention claims. The paper reports 5-fold cross-validation averages for downstream regression/classification and says experiments use fixed random seeds, but it does not appear to report variance, confidence intervals, error bars, or statistical significance across independent seeds or folds. This makes the claimed stability difficult to distinguish from a single-seed or fold-averaged trend. The paper does address one important completeness concern by providing final-epoch tables in the appendix, which is useful because collapse is specifically a late-training phenomenon and best-epoch reporting could hide it. However, the main evidence still relies heavily on downstream R2/F1 performance curves and final downstream scores. The paper also includes a diagnostic based on correlation between unrelated/noise data after transformation, which is more directly related to the proposed collapse mechanism, but it does not seem to provide a systematic collapse-prevention metric such as rank/singular-value behavior, covariance degeneracy, collapse frequency across runs, or statistical tests of the noise-correlation diagnostic. Overall, the results are suggestive and include relevant final-epoch evidence, but the lack of uncertainty estimates and limited direct collapse quantification are a soundness weakness.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The experimental protocol reports downstream evaluation using Ridge Regression with R2 for regression and SVC with average F1 for classification under 5-fold cross-validation.
- paper: The reproducibility statement says experiments use fixed random seeds and 5-fold cross-validation, but the provided summary does not indicate reported standard deviations, error bars, confidence intervals, or significance tests across seeds/folds.
- paper: The appendix includes final-epoch result tables for synthetic and real-world datasets, which helps evaluate whether NR-DCCA remains stable at the end of training rather than only at a selected best epoch.
- paper: The paper uses downstream task performance curves to show collapse/stability and also reports a diagnostic that transformed unrelated data exhibit increasing correlation in collapsed DCCA-based models.
- inference: Because collapse prevention is a stability claim over training and randomness, evidence based mainly on fixed-seed curves and fold-averaged downstream scores without uncertainty estimates is statistically weaker than multi-seed results with variance/significance and direct collapse metrics.

### Q4

**Question:** Do the ablations adequately isolate the claimed mechanism of noise regularization? In particular, does the paper test variants such as no noise regularizer, different noise distributions/scales, applying the penalty to inputs versus hidden/output representations, replacing the correlation penalty with simpler norm/Jacobian/variance/rank penalties, or measuring whether the regularizer actually preserves rank/singular values and prevents learned cross-view “model correlation”?

**Answer:** No. The ablations only partially probe the mechanism. The paper compares NR-DCCA against unregularized DCCA-style baselines, varies the noise-regularization weight alpha, tests ridge regularization as an alternative regularizer, and extends the same idea to DGCCA. These are useful checks, but they do not adequately isolate the claimed mechanism that noise regularization preserves a full-rank transformation and prevents learned model correlation. The paper appears not to test different noise distributions or noise scales beyond the regularization weight, not to compare applying the penalty at inputs versus hidden/output layers, not to replace the correlation-based penalty with simpler norm/Jacobian/variance/rank/spectral penalties, and not to directly measure singular values, ranks, Jacobian spectra, or whether the learned neural transformations remain full-rank in an ordinary linear-algebraic sense. The diagnostic that transformed unrelated/noise data become correlated is relevant, but it is not enough to establish that the proposed penalty specifically works through rank preservation rather than through a more generic smoothing, variance, or capacity-control effect. This weakens the soundness of the mechanistic claim, even if the empirical performance gains may still be real.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The method defines NR-DCCA by generating i.i.d. Gaussian white noise for each view and penalizing the absolute difference between Corr(f_k(X_k), f_k(A_k)) and Corr(X_k, A_k), i.e. the core intervention is a correlation-with-noise penalty at the transformed representation level.
- paper: The reported ablations include varying the NR-DCCA regularization weight alpha on CUB, with the paper stating that too-large alpha slows convergence while too-small alpha leaves collapse.
- paper: The appendix also varies ridge regularization r for DCCA on CUB and reports that ridge regularization does not prevent collapse.
- paper: The paper reports diagnostics that transformed unrelated data can show increasing correlation in collapsed DCCA-based models, and uses this to support the claim of learned model correlation.
- paper: The paper itself lists future work on further investigating the proposed neural-network “full-rank” definition, comparing it with orthogonalization and weight decay, and understanding what and how neural networks are regularized through noise.
- inference: Because the paper’s neural-network “full-rank” property is defined via the proposed noise-regularization objective itself, rather than independently validated by rank/singular-value/Jacobian measurements, the ablation evidence is partly circular for the mechanism claim.
- inference: The absence, in the provided paper map, of ablations over noise distribution, noise scale, penalty location, or alternative regularizers such as norm, Jacobian, variance, rank, or spectral penalties suggests the paper does not rule out simpler explanations for the observed stabilization.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall / ICLR format:** Pages use an ICLR-style header, margins, page numbers, and readable single-column layout. Visually inspectable overall, but several figures are too small/dense for comfortable review.

- **Page 1:** Title is readable but has awkward line breaks/hyphenation (“Canoni- / cal”, “Regular- / ization”) and very wide letter spacing. Abstract and keywords are readable.

- **Pages 2, 5, 6, 7, 8:** Yellow-highlighted text appears throughout the manuscript. This is distracting and not appropriate for a clean ICLR submission unless intentionally part of an annotated draft.

- **Page 2, Figure 1:** Main diagram is generally legible, but small internal labels may be hard to read at normal zoom. Caption is connected but minimal (“Correlations in CCA and DCCA”) and could better explain the two panels.

- **Pages 4–6, equations:** Displayed equations are mostly readable and well aligned. Some inline math-heavy sentences are dense but not visually broken. Equation numbering appears consistent.

- **Page 5, Figure 2:** Caption is informative and connected to the diagram. However, the figure contains many small labels/arrows/text blocks; details are difficult to inspect without zooming.

- **Page 5:** Section title “DCCA with Noise Regularization(NR-DCCA)” is missing a space before the parenthesis.

- **Page 7:** No figures/tables on this page. Text is readable, but the highlighted sentence and colored appendix references are visually distracting.

- **Page 8, Figure 3:** Caption is clear and connected. The diagram’s internal labels are quite small; zooming is needed to read details.

- **Page 8, Figure 4:** Caption is informative, but plot legends, axis labels, and tick labels are small, especially in the three small correlation subplots. Some curves/colors may be hard to distinguish at print size.

- **Page 8, Figure 5:** Multi-panel plot is too compressed; legends, axis labels, and markers are difficult to read. This figure would benefit from enlargement or moving to appendix/full-width formatting with fewer panels per row.

- **Tables:** No tables are visible in the provided pages, so table legibility cannot be assessed.

- **Captions overall:** Captions generally describe the visual content and are placed appropriately, but several could be more explanatory, especially for dense diagrams/plots.

- **Typography/layout issues:** Main text is readable, but pages with multiple figures—especially page 8—feel crowded. Hyperlink colors are acceptable, though red appendix/equation links plus yellow highlighting make the page visually busy.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

### Q2

**Question:** Please inspect the appendix PDF pages containing Tables 2–3 and Figures 7–12 for presentation quality: are the tables/plots legible, captions sufficiently explanatory, and formatting/layout easy to review?

**Answer:** The appendix materials are generally reviewable and legible. Tables 2–3 appear to be formatted as conventional full-width result tables with method names, dataset/common-rate columns, numeric mean/std-style entries, and highlighted best values, which makes them interpretable. Figures 7–12 are also presented as standard multi-panel plots with axes, legends, and captions indicating the experiment being varied, such as ridge regularization, noise-regularization weight, representation visualization, and DGCCA/NR-DGCCA behavior. However, the appendix is somewhat dense: several plots/tables compress many methods, datasets, and training curves into limited space, so some labels and legends require close reading, and the captions are mostly descriptive rather than fully self-contained. Overall, this is a minor presentation strength: the appendix is usable for verification, but the readability of dense result displays could be improved.

**Impact:** strength, C1, confidence=medium

**Evidence:**
- paper: The appendix contains Tables 2–3 reporting final-epoch synthetic and real-world results, and Figures 7–12 covering ridge-regularization ablation, NR-DCCA regularization-weight ablation, representation visualizations, and DGCCA extension experiments.
- paper: The relevant appendix pages present these items in standard table/plot formats with captions identifying the experiment and plotted quantities, making the results inspectable.
- inference: Because the appendix packs many methods, datasets, common-rate settings, and training curves into a small number of pages, the layout is informative but visually dense; this slightly reduces ease of review but does not prevent interpretation.

# Q&A Trajectory

## Contribution

### Q1

**Question:** How novel is the paper's core contribution relative to prior work on weakly supervised semantic segmentation, noisy-label segmentation with learned confusion/transition matrices, and complementary-label learning? In particular, is combining positive coarse labels, negative/complementary coarse labels, and pixel-wise confusion-matrix modeling a meaningfully new technical contribution, or mostly an incremental recombination of existing ideas?

**Answer:** Unable to complete the novelty assessment with the required evidence because no paper-text or scholarly-retrieval observations were returned after the requested search. Based only on the provided paper map, the claimed contribution appears to be a specific combination of known ingredients—weak/coarse supervision for segmentation, complementary/negative-label learning, and learned pixel-wise confusion matrices for noisy segmentation labels—rather than an obviously new technical paradigm. The paper’s own positioning claims novelty in jointly exploiting positive and complementary coarse annotations and in applying per-image pixel-wise confusion-matrix modeling to noisy coarse annotations. However, without retrieved prior-work evidence, I cannot verify whether this joint formulation had already been substantially explored. My reviewer-style judgment is therefore that the contribution is likely incremental-to-moderate: potentially novel as a particular integration for coarse semantic segmentation, but not clearly a major conceptual advance over existing weak-supervision, complementary-label, and noisy-label transition/confusion-matrix methods.

**Impact:** weakness, C2, confidence=low

**Evidence:**
- paper: The summary reports that the method trains from noisy positive and negative coarse annotations using two coupled CNNs: a segmentation network estimating true pixel-label distributions and a coarse-annotation network estimating pixel-wise confusion matrices.
- paper: The related-work summary says the paper itself acknowledges prior weakly supervised segmentation using scribbles, boxes, points, image-level labels, and coarse labels; prior complementary-label learning; and prior noisy-label learning with transition or confusion matrices.
- paper: The paper’s asserted novelty, according to the summary, is that previous segmentation methods used either target-object weak annotations or complementary labels, while this work exploits both simultaneously, and that it is the first application of per-image pixel-wise confusion-matrix modeling to noisy coarse-annotation learning.
- paper: The conclusion summary states that implementation requires only adding a complementary-label learning term to the loss function, which weakens the impression of a deeply new technical mechanism.
- retrieval: No external scholarly retrieval results were available in the tool observations, so prior-work overlap could not be independently verified.
- inference: Because each main component appears to come from an established literature and the novelty claim is mainly about combining them for the specific coarse-segmentation setting, the contribution is best viewed as an incremental recombination unless external evidence shows that this combination was previously absent and empirically important.

## Soundness

### Q1

**Question:** Do the experiments report variance/significance over multiple runs or splits, and are the weak-supervision baselines trained/evaluated under comparable annotation budgets and using reasonably current implementations/settings?

**Answer:** The experimental reporting is only partially sound on this point. The main MNIST and Cityscapes tables report results as mean ± variation, so some variance is reported. However, the paper text available here does not specify the number of runs, random seeds, or alternative train/test splits behind those error bars, and I found no evidence of statistical significance tests. Comparability of weak-supervision baselines is also not fully established: the paper compares against methods using different annotation types such as scribbles, coarse labels, and boxes, while the proposed method can use both positive and negative coarse annotations, which may constitute a different annotation budget. The paper lists both older baselines such as GrabCut, LazySnapping, BoxSup, and ScribbleSup and newer ones such as CycleMix, CoarseSup, LC-MIL, and L2G, but it does not clearly document whether current official implementations, tuned hyperparameters, or matched training settings were used. This weakens the strength of the empirical claims, especially claims of state-of-the-art performance across weak-supervision regimes.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The comparison-methods section states that the experiments assume no expert consensus label is available during training and compare against multiple weakly supervised and semi-supervised methods, including GrabCut, LazySnapping, scribble-guided methods, coarse-annotation methods, and box-level methods; evaluation uses mIoU against expert consensus labels.
- paper: Table 1 and Table 2 report mIoU values with ± terms, e.g. the proposed method reports 82.5 ± 0.1 on MNIST and 68.3 ± 0.2 on Cityscapes in Table 1, and weak-supervision comparisons in Table 2 also include ± terms.
- paper: The paper explicitly says the weak-supervision comparison uses different ways of annotation, including scribble-guided annotations, coarse annotations, and box-level annotations, rather than a single matched annotation budget across all methods.
- inference: Because the paper reports ± values but does not state the number of runs/splits or conduct significance tests in the inspected evidence, the variance reporting is incomplete. Because annotation modalities and positive/negative supervision differ across methods, the baseline comparison may not isolate algorithmic superiority from annotation-budget differences.

### Q2

**Question:** Does the paper provide a convincing technical justification or ablation for the probabilistic model components—especially the pixel-wise confusion matrix, trace regularization, and complementary negative-label loss—and does it address possible identifiability/degenerate-solution issues when jointly learning true labels and annotation noise from only coarse labels?

**Answer:** No. The paper gives a plausible probabilistic formulation, but the soundness support for its key modeling components is incomplete. It defines a pixel-wise confusion-matrix model for noisy positive coarse labels, adds trace regularization to encourage separation between true labels and annotation noise, and adds a complementary negative-label loss in the final objective. However, the experimental ablation evidence appears to isolate mainly the use of negative annotations, not the individual necessity of the pixel-wise confusion matrix, the trace regularizer, or the exact complementary-loss formulation. The reported “with vs. without negative annotation” comparison supports that negative labels help, but it does not establish that the proposed probabilistic decomposition is identifiable or that the trace regularizer prevents degenerate solutions. This is a significant soundness concern because the method jointly learns the latent true segmentation distribution and annotation-noise/confusion processes from coarse labels only; without stronger theory, constraints, or ablations, alternative decompositions could explain the observed coarse labels equally well.

**Impact:** weakness, C3, confidence=medium

**Evidence:**
- paper: The method section formulates training with no ground-truth masks during training and introduces a likelihood over observed positive and negative coarse annotations, with a segmentation network estimating the latent true segmentation distribution and a coarse-annotation network estimating pixel-wise confusion matrices.
- paper: The paper defines the positive coarse-label objective using predicted noisy-label distributions and observed positive annotations, then adds a trace regularization term that is described as encouraging separation between annotation noise and the true label distribution.
- paper: The final objective sums the positive annotation loss and the complementary negative annotation loss, so the main model relies on several coupled components: latent true-label prediction, pixel-wise confusion matrices, trace regularization, and negative-label learning.
- paper: The main ablation reported in the paper compares the method with and without negative annotation: Table 1 reports improvements from 77.2 to 82.5 mIoU on MNIST and from 62.3 to 68.3 mIoU on Cityscapes when negative annotations are included. This supports the utility of negative annotations but does not separately validate the confusion-matrix parameterization or trace regularization.
- paper: The discussion/future-work section notes that imposing structures on confusion matrices and transition matrices would be valuable, suggesting that the current unconstrained or lightly constrained noise-modeling components are not fully justified or resolved.
- inference: Because both the true segmentation distribution and annotation-noise model are learned from observed coarse labels, the model has an inherent non-identifiability risk: different combinations of true-label predictions and confusion matrices could produce similar observed coarse-label likelihoods. The paper does not appear to provide a theorem, diagnostic, constraint analysis, or ablation showing that the learned decomposition avoids such degenerate explanations.

### Q3

**Question:** Are the coarse positive/negative annotations in the main MNIST and Cityscapes experiments synthetic or real, and does the paper provide enough detail to rule out evaluation artifacts such as annotation generation being too closely tied to ground-truth masks, small/unstable test sets, or train/test leakage—especially for the very small LES-AV retinal experiment?

**Answer:** The main MNIST and Cityscapes positive/negative coarse annotations appear to be synthetic, not real human coarse annotations: the experimental setup describes generating coarse labels through morphological transformations such as thinning, thickening, fractures, and over-segmentation. The LES-AV retinal experiment is described differently: it uses practical positive and negative coarse annotations from an experienced annotator, but only 22 images total with an 18/4 train/test split. Overall, the paper does not provide enough detail to confidently rule out evaluation artifacts. In particular, for MNIST and Cityscapes, the synthetic coarse annotations are derived from or closely related to the available ground-truth masks, so strong performance may partly reflect how well the method fits the annotation-generation process rather than real coarse-label noise. For LES-AV, the test set of 4 images is extremely small, and the paper summary does not indicate repeated splits, cross-validation, variance/error bars, subject-level leakage checks, or sufficiently detailed annotation protocol controls. This is a soundness weakness because the empirical claims rely heavily on synthetic supervision and a very small real-data validation, making the reported gains potentially unstable or inflated by construction choices.

**Impact:** weakness, C3, confidence=medium

**Evidence:**
- paper: The experiment setup states that synthetic positive and negative coarse labels are generated with morphological transformations such as thinning, thickening, fractures, and over-segmentation for the MNIST-derived and Cityscapes experiments.
- paper: The dataset description states that MNIST segmentation uses 60,000 training and 10,000 testing images with masks derived by thresholding digit intensity, and Cityscapes is used for urban scene segmentation.
- paper: The LES-AV retinal dataset is described as containing 22 fundus photographs with manual vessel/artery/vein annotations, using 18 training and 4 testing images.
- paper: The retinal section states that an experienced annotator provides practical positive and negative coarse annotations for each LES-AV sample, and that five coarse-annotation quality levels are constructed.
- inference: Because the main coarse annotations are synthetically generated from segmentation masks via morphological operations, the annotation noise model may be too aligned with the evaluation ground truth and may not reflect real human coarse labeling. The paper also gives insufficient evidence of robustness checks for the 4-image LES-AV test set, such as repeated splits, confidence intervals, or leakage controls.

### Q4

**Question:** Does the paper specify implementation details that make the pixel-wise confusion matrices and complementary transition matrices valid and scalable—e.g., normalization/constraints to ensure proper probability matrices, architecture choices for predicting L×L matrices per pixel, hyperparameter selection for trace regularization, and whether these settings are ablated or tuned on validation data?

**Answer:** No. The paper gives the high-level probabilistic formulation for pixel-wise L×L confusion matrices and complementary transition matrices, but it does not appear to provide enough implementation detail to establish that these matrices are valid probability matrices or scalable in practice. It defines the pixel-wise confusion-matrix model in the method section, uses a positive coarse-label cross-entropy objective, adds trace regularization, and combines this with a complementary negative-label loss. However, the available paper evidence does not specify key details such as how each per-pixel L×L matrix is normalized or constrained, whether rows or columns are made stochastic by softmax, what network head predicts the L×L matrix per pixel, how memory/computation scales with large L and high-resolution segmentation, how the trace-regularization coefficient is chosen, or whether these choices are tuned on validation data. The experimental ablations mainly compare using positive annotations alone versus positive plus negative annotations, different supervision regimes, and annotation-quality levels; they do not appear to ablate the matrix parameterization, normalization, trace-regularization strength, or complementary transition-matrix design. This weakens soundness because the method’s central claim depends on learning meaningful pixel-wise annotation-noise matrices, but the paper does not sufficiently document or validate the mechanisms that make those matrices identifiable, probabilistically valid, or robustly trainable.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The method section is described as defining a probabilistic model with pixel-wise L by L confusion matrices, where Equation 2 models the probability of observing a coarse label given the true pixel label and image.
- paper: The method section adds a trace regularization term to the positive coarse-label loss in Equation 4 and combines positive and complementary negative losses in Equation 6.
- paper: The experimental ablations summarized for the paper include comparisons with and without negative annotations, weak/strong/semi-supervised settings, and sensitivity to coarse-annotation quality, but not ablations of matrix normalization, architecture, trace-regularization hyperparameters, or transition-matrix constraints.
- paper: The conclusion lists future work on imposing structure on confusion matrices and transition matrices, suggesting that the current formulation does not fully address structured or constrained matrix design.
- inference: Because the central objects are per-pixel L×L probability matrices, missing details about stochastic normalization, network parameterization, hyperparameter selection, and computational scaling are consequential for reproducibility and for assessing whether the learned matrices are valid rather than arbitrary latent factors.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall visual inspectability:** The paper is generally easy to visually inspect in an ICLR-style format: consistent margins, clear section headings, readable body text, and page numbers. The header indicates camera-ready status (“Published as a conference paper at ICLR 2024”), not an anonymous submission.

- **p.1:** Text-only page is clean and readable. Title is prominent; abstract is legible though quite dense as one long paragraph. No figure/table issues.

- **p.2 / Figure 1:** The system schematic is informative and well connected to the caption, but many internal labels, arrows, and math symbols are very small at page scale. The caption explains the components clearly, but the visual itself requires zooming for full readability.

- **p.3–5 / Equations:** Equations are generally well formatted and numbered. Some multi-symbol expressions are dense, especially around Eq. (1)–(5), but they appear within margins and are not obviously broken. Inline math is heavy and can make text visually dense.

- **p.6:** Layout remains clean; no figures/tables. Subsections are easy to locate. Dense paragraphs but readable.

- **p.7 / Figure 2:** The MNIST visual grid is useful and caption is detailed, but subpanel labels, colorbars, and fine pixel-level details are small. The caption is informative and maps labels A1–G2 to content, though it is long.

- **p.7 / Tables 1–2:** Tables are legible, compact, and aligned. Captions clearly state metrics and datasets. Some method names/citations in Table 2 are tight but readable.

- **p.8 / Figures 3–4:** The plots are too small for comfortable inspection; axis labels, legends, tick labels, and data markers are difficult to read without zooming. Captions explain the intent, but the visual details are not very legible at printed page size.

- **p.8 / Table 3:** Table is mostly readable, but the side-by-side MNIST/Cityscapes layout is dense and uses many vertical rules; caption is informative. Slightly larger table text or more spacing would help.

- **Captions:** Captions are generally informative and directly connected to the figures/tables. Several are long and descriptive, which helps interpretation but contributes to page density.

- **Formatting/layout issues:** No major margin overflow or broken floats visible. Main presentation weakness is small figure text/legends in complex schematics and plots. Body text is readable but visually dense due to long paragraphs and heavy math notation.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

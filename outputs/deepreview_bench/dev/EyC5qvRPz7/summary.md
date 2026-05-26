# Paper Map

```text
PAPER MAP
Title: Emerging Semantic Segmentation from Positive and Negative Coarse Label Learning
Authors: unknown
Venue: ICLR 2024
Submission date: 2025-08-25

SECTIONS
[s1] Abstract
Summary: The abstract proposes training semantic segmentation CNNs from noisy positive and negative coarse annotations instead of dense pixel labels. It describes a two-CNN approach for estimating true segmentation distributions and annotation confusion matrices, and reports experiments on MNIST-derived segmentation, Cityscapes, and retinal images.
Key items:
- problem: Pixel-level segmentation labels are costly, time-consuming, error-prone, and especially expensive in medical imaging.
- method_component: The method uses two coupled CNNs to learn true segmentation distributions from noisy coarse annotations.
- method_component: Complementary label learning is added to encourage estimation from negative label distributions.
- dataset: Experiments use a toy MNIST segmentation dataset, Cityscapes, and retinal images.
- claim: The abstract states that the method outperforms state-of-the-art methods, especially when coarse annotations are sparse relative to dense annotations.

[s2] Introduction
Summary: The introduction motivates coarse annotations as cheaper alternatives to dense masks and discusses segmentation label noise, weak supervision, semi-supervision, and medical imaging needs. It states the paper's contribution as an end-to-end supervised segmentation method using positive and negative noisy coarse annotations with two coupled CNNs.
Key items:
- motivation: Foundation segmentation models may perform poorly on irregular, weak-boundary, small, or low-contrast objects, motivating task-specific annotations.
- method_component (Figure 1): The architecture contains a segmentation network estimating true segmentation probabilities and a coarse annotation network estimating pixel-wise confusion matrices for positive and negative annotations.
- claim: The paper describes the method as the first end-to-end supervised segmentation method estimating true labels from noisy coarse annotations.
- claim: The method is designed to disentangle annotation errors from true labels even when the ratio of coarse annotation is small.
- dataset: The evaluation plan includes simulated annotations on MNIST, Cityscapes multi-class segmentation, and medical retinal image segmentation.

[s3] Related Work
Summary: This section reviews weakly supervised segmentation with scribbles, boxes, points, image-level labels, and coarse labels; complementary label learning; and learning from noisy labels using transition or confusion matrices. It positions the paper as using both target and complementary coarse annotations while explicitly modeling noisy coarse labels.
Key items:
- baseline: Reviewed weak-supervision methods include ScribbleSup, CycleMix, BoxSup, L2G, point supervision, and image-level supervision.
- method_component: Complementary Label Learning uses labels indicating classes a sample does not belong to.
- claim: The paper states that previous segmentation methods focus on either target-object weak annotations or complementary labels, while this work exploits both simultaneously.
- method_component: The section connects the method to noisy-label models using probability transition matrices and pixel-wise confusion matrices.
- claim: The paper states this is the first application of per-image pixel-wise confusion-matrix modeling to noisy coarse annotation learning.

[s4] Method
Summary: The method formulates learning an unobserved true segmentation distribution from images with positive and/or negative noisy coarse annotations and no ground-truth labels during training. It defines a probabilistic model with pixel-wise confusion matrices, a segmentation network, a coarse annotation network, positive coarse-label loss, negative complementary-label loss, and a final combined objective.
Key items:
- problem (Section 3.1): Training data consist of images with noisy objective and complementary coarse labels; true segmentation masks are unavailable during training.
- method_component (Equation 1): The probabilistic model factorizes the likelihood of observed coarse labels across annotations and pixels.
- method_component (Equation 2): A pixel-wise L by L confusion matrix models the probability of observing a coarse label given the true pixel label and image.
- method_component (Equation 3): The positive coarse-label objective uses cross-entropy between predicted noisy-label distributions and observed positive coarse annotations.
- method_component (Equation 4): A trace regularization term is added to the positive coarse-label loss to encourage separation of annotation noise and true label distribution.
- method_component (Equation 6): The final objective sums the positive annotation loss and complementary negative annotation loss.

[s5] Experiments: Setup, Synthetic Annotations, Baselines, and Metrics
Summary: This section describes the experimental datasets, the generation of synthetic coarse annotations, compared methods, ablations, and the evaluation metric. It uses MNIST-derived segmentation, Cityscapes, and LES-AV retinal vessel segmentation, with synthetic positive and negative coarse annotations produced through morphological transformations.
Key items:
- dataset (Section 4.1): MNIST segmentation uses 60,000 training and 10,000 testing grayscale digit images with segmentation labels derived by thresholding intensity at 0.5.
- dataset (Section 4.1): Cityscapes contains 5,000 fine annotations and 20,000 coarse annotations for urban scene segmentation.
- dataset (Section 4.1): LES-AV contains 22 retinal fundus photographs with manual retinal vessel, artery, and vein annotations; the paper uses 18 training and 4 testing images.
- method_component (Section 4.2): Synthetic positive and negative coarse labels are generated with morphological transformations such as thinning, thickening, fractures, and over-segmentation.
- baseline (Section 4.3): Compared methods include GrabCut, LazySnapping, ScribbleSup, CycleMix, CoarseSup, LC-MIL, BoxSup, and L2G.
- metric (Section 4.3): The evaluation metric is mean Intersection over Union between estimated segmentation and expert consensus label.

[s6] Segmentation Performance and Annotation-Quality Sensitivity
Summary: This section reports MNIST and Cityscapes results for two-step interactive-mask approaches, weakly supervised baselines, strong and semi-supervised settings, and varying coarse-annotation quality. It also visualizes estimated labels, confusion matrices, transition matrices, and sensitivity curves.
Key items:
- result (Table 1): Using positive and negative annotations, the method reports 82.5 mIoU on MNIST and 68.3 mIoU on Cityscapes; without negative annotations it reports 77.2 and 62.3.
- baseline (Table 1): GrabCut plus FCN reports 75.2 mIoU on MNIST and 53.6 on Cityscapes; LazySnapping plus FCN reports 78.5 and 59.4.
- result (Table 2): Against weakly supervised methods, the coarse version of the method reports 82.5 mIoU on MNIST and 68.3 on Cityscapes.
- ablation (Table 1): The paper compares the method with and without negative annotation.
- ablation (Table 3): The paper compares weak, strong, and semi-supervised settings using mask-level and coarse annotations.
- result (Table 3): The semi-supervised setting reports 88.7 mIoU on MNIST and 73.3 on Cityscapes, described as about 2 percentage points higher than the strongly supervised approach.

[s7] Experiments on Retinal Vessel Segmentation
Summary: This section applies the method to LES-AV retinal vessel segmentation with real coarse positive and negative annotations from an experienced annotator. It also constructs five annotation-quality levels and evaluates performance under different supervision settings.
Key items:
- dataset (Section 4.6): LES-AV retinal fundus images are used for binary vessel segmentation.
- method_component (Section 4.6): An experienced annotator provides practical positive and negative coarse annotations for each LES-AV sample.
- ablation (Section 4.6): The paper creates five positive and negative coarse-annotation ratio levels from level-1, close to scribble, to level-5, close to ground truth.
- result (Figure 5): The paper reports that performance gradually improves as the retinal coarse-annotation ratio increases, with a significant increase from level-1 to level-2.
- result (Table S2): The paper states that the weakly supervised retinal approach achieves comparable results to strong supervision and that adding extra coarse annotations improves the result by 3%.

[s8] Discussion and Conclusion
Summary: The conclusion states that the paper introduces an algorithm for recovering expert consensus label distributions from noisy coarse annotations and that experiments on synthetic and real datasets show segmentation accuracy and robustness to annotation quality and label noise. It lists future directions involving structured confusion and transition matrices and learning from difficult cases or patches with coarse annotations.
Key items:
- claim: The paper states that the method recovers expert consensus label distributions from noisy coarse annotations.
- claim: The paper states that implementation requires only adding a complementary label learning term to the loss function.
- claim: The paper states that experiments on synthetic and real datasets show superior performance over common WSL and SSL methods in segmentation accuracy and robustness.
- stated_limitation: Future work should consider imposing structures on confusion matrices and transition matrices to broaden applicability to scribble or spot annotations.
- stated_limitation: The paper identifies learning only from coarse annotations in difficult cases or difficult image patches as a valuable next step.

GLOBAL INDEX
Claims:
- [s1] The abstract states that the method outperforms state-of-the-art methods, especially when the ratio of coarse annotations is small.
- [s2] The paper describes the method as the first end-to-end supervised segmentation method estimating true labels from noisy coarse annotations.
- [s2] The method is claimed to disentangle annotation errors from true labels even with sparse coarse annotations.
- [s3] The paper states that it exploits both target and complementary weak annotations simultaneously.
- [s8] The paper states that experiments show superior performance over common WSL and SSL methods in accuracy and robustness.
Method components:
- [s2] Two coupled CNNs: a segmentation network and a coarse annotation network.
- [s4] Pixel-wise L by L confusion matrices model noisy positive and negative coarse labeling processes.
- [s4] Positive coarse-label NLL/cross-entropy objective.
- [s4] Trace regularization on estimated confusion matrices.
- [s4] Complementary negative coarse-label learning using a transition matrix.
- [s4] Final loss is the sum of positive annotation loss and complementary annotation loss.
- [s5] Synthetic coarse annotations are generated with morphological transformations.
Datasets:
- [s5] MNIST-derived segmentation dataset with thresholded digit masks.
- [s5] Cityscapes urban scene segmentation dataset.
- [s5] LES-AV retinal fundus vessel segmentation dataset.
Baselines:
- [s5] GrabCut plus FCN.
- [s5] LazySnapping plus FCN.
- [s5] ScribbleSup.
- [s5] CycleMix.
- [s5] CoarseSup.
- [s5] LC-MIL.
- [s5] BoxSup.
- [s5] L2G.
- ... 2 more
Ablations:
- [s6] Ours without negative annotation versus ours with positive and negative annotations.
- [s6] Scribble versus coarse annotation inputs for the proposed method.
- [s6] Weak, strong, and semi-supervised training settings with different counts of mask and coarse annotations.
- [s6] Sensitivity to coarse-annotation area ratios including a 0.01 scribble-like ratio.
- [s7] Five retinal annotation-quality levels from level-1 to level-5.
Metrics:
- [s5] Mean Intersection over Union, mIoU.
Results:
- [s6] Table 1: Ours with positive and negative annotations reports 82.5 mIoU on MNIST and 68.3 on Cityscapes.
- [s6] Table 1: Ours without negative annotation reports 77.2 mIoU on MNIST and 62.3 on Cityscapes.
- [s6] Table 2: Ours with coarse annotations reports higher mIoU than listed weakly supervised baselines on MNIST and Cityscapes.
- [s6] Table 3: Weak, strong, and semi-supervised settings report 82.5, 86.2, and 88.7 mIoU on MNIST.
- [s6] Table 3: Weak, strong, and semi-supervised settings report 68.3, 71.7, and 73.3 mIoU on Cityscapes.
- [s7] Figure 5: Retinal performance is stated to improve as coarse-annotation quality level increases.
- [s7] Table S2: Retinal WSL is stated to be comparable to strong supervision, and extra coarse annotations improve the result by 3%.
Stated limitations:
- [s8] Future work should impose structure on confusion matrices and transition matrices for broader applicability to scribble or spot annotations.
- [s8] Learning only from coarse annotations in difficult cases or difficult patches is identified as a valuable next step.
```

# Paper Map

```text
PAPER MAP
Title: Preventing Model Collapse in Deep Canonical Correlation Analysis by Noise Regularization
Authors: Anonymous authors
Venue: ICLR
Submission date: 2024-11-01

SECTIONS
[s1] Introduction
Summary: The section introduces multi-view representation learning, CCA, DCCA, and the observed model collapse issue in DCCA-based methods. It states that NR-DCCA uses noise regularization to constrain neural networks to be “full-rank” and prevent collapse.
Key items:
- problem: DCCA-based methods can show drastic downstream performance drops as training proceeds, called model collapse.
- motivation: Early stopping is presented as difficult because deciding when to stop is challenging.
- claim (Figure 1): The paper claims model collapse comes from overly powerful DNN transformations creating model correlation rather than view correlation.
- method_component: NR-DCCA adds a noise regularization approach tailored to DCCA-based methods.
- claim: The paper claims the full-rank property of CCA transformations is key to preventing model collapse.
- claim: The paper claims the noise regularization can also be applied to other DCCA-based methods such as DGCCA.

[s2] Related Works
Summary: The section surveys multi-view representation learning, CCA and DCCA variants, and noise regularization. It positions the work as focusing on CCA/DCCA and using noise regularization specifically to prevent DCCA model collapse.
Key items:
- other: MVRL methods discussed include DMF-MVC, MDcR, CPM-Nets, AE2-Nets, DUA-Nets, and MVTCAE.
- baseline: CCA-related methods discussed include CCA, KCCA, DCCA, DGCCA, DCCAE, DVCCA, DTCCA, MCCA, GCCA, and TCCA.
- claim: The section states that the model collapse issue of DCCA-based methods has not been explored and addressed.
- other: Prior noise regularization is described for supervised generalization, adversarial training, and autoencoders.
- claim: The section states that using noise regularization for DCCA-based methods to prevent model collapse has not been studied.

[s3] Preliminaries
Summary: The section defines the MVRL setting, reviews CCA and DCCA objectives, and demonstrates the DCCA model collapse phenomenon. It distinguishes CCA linear transformations from DCCA neural-network transformations.
Key items:
- method_component (Equation 1): MVRL learns a transformation that maps multiple views into a unified representation.
- method_component (Equations 2-4): CCA maximizes correlations between linearly projected views and concatenates projected views as the representation.
- method_component (Equation 5): DCCA replaces CCA transformation matrices with neural networks and optimizes view correlations by backpropagation.
- problem: DCCA performance can become worse than CCA and simple feature concatenation after collapse.
- result (Figure 4): The paper reports that transformed unrelated data exhibit increasing correlation in collapsed DCCA-based models.
- claim (Appendix A.6.1): The paper states that full-rank DCCA representations alone do not prevent model collapse.

[s4] DCCA with Noise Regularization (NR-DCCA)
Summary: The section presents NR-DCCA, which generates Gaussian white noise for each view and penalizes changes in correlation between real data and noise after neural transformation. It provides theoretical analysis connecting invariance of correlation with noise to full-rank transformations in CCA and defines an analogous “full-rank” property for neural networks.
Key items:
- method_component: NR-DCCA generates i.i.d. Gaussian white noise with the same shape as each input view.
- method_component (Equation 6): The NR loss penalizes the absolute difference between Corr(f_k(X_k), f_k(A_k)) and Corr(X_k, A_k).
- claim (Proposition 3): For full-rank square linear transformations in CCA, correlation between data and noise is invariant before and after transformation.
- claim (Proposition 4): If the correlation invariance condition holds for a square CCA transformation, the transformation must be full-rank.
- method_component (Definition 2): A neural network f_k is defined as “full-rank” when the NR loss term zeta_k equals 0.
- claim: The section states that enforcing the neural network to share the correlation-with-noise property of full-rank CCA transformations eliminates model collapse.

[s5] Numerical Experiments
Summary: The section evaluates NR-DCCA on synthetic and real-world datasets using downstream regression or classification after unsupervised representation learning. It compares against concatenation, CCA-based methods, DCCA-based methods, and MVTCAE.
Key items:
- dataset (Figure 3): Synthetic datasets are generated from a “God Embedding” with common rates from 0% to 100%.
- dataset: Real-world datasets include PolyMnist, CUB, and Caltech101.
- baseline: Baselines include CONCAT, CCA, PRCCA, KCCA, DCCA, DGCCA, DCCAE/DGCCAE, DCCA PRIVATE/DGCCA PRIVATE, and MVTCAE.
- metric: Regression uses Ridge Regression with R2; classification uses SVC with average F1, both under 5-fold cross-validation.
- result (Figures 4 and 5): On synthetic datasets, NR-DCCA is reported to maintain stable performance while DCCA-based methods collapse during training.
- result (Figure 6): On real-world datasets, NR-DCCA is reported to show competitive and stable performance, with stronger collapse observed for DCCA-based methods as PolyMnist views increase.

[s6] Conclusion and Reproducibility Statement
Summary: The conclusion restates that noise regularization is proposed for DCCA to prevent model collapse and that the approach is supported by theory and experiments. The reproducibility statement describes fixed seeds, 5-fold cross-validation, implementation packages, dataset availability, and supplementary code and appendix.
Key items:
- claim: NR-DCCA is stated to inherit merits of CCA and DCCA and achieve stable, consistent performance on synthetic and real-world datasets.
- claim: The proposed noise regularization is stated to generalize to DGCCA.
- stated_limitation: Future work includes exploring noise regularization in contrastive learning and generative models.
- stated_limitation: Future work includes further investigating the “full-rank” neural-network definition and differences from orthogonalization and weight decay.
- stated_limitation: The paper states it is interesting but challenging to investigate what and how neural networks are regularized through noise.
- other: Experiments use fixed random seeds, 5-fold cross-validation, CCA-Zoo implementations, the original MVTCAE implementation, and PyTorch.

[s7] Appendix
Summary: The appendix provides proofs, dataset and baseline details, hyper-parameter settings, complexity analysis, representation visualizations, DGCCA extension experiments, and final-epoch result tables. It also reports detailed synthetic and real-world dataset configurations.
Key items:
- dataset (Appendix A.5): Synthetic data use n=4000, d=100, six common-rate groups, 2000 train and 2000 test tuples, and 50 downstream regression tasks.
- dataset (Appendix A.5): PolyMnist has 5 MNIST-image views; CUB uses 1024-d visual and 300-d text features; Caltech101 uses HOG, GIST, and SIFT views.
- ablation (Figure 7): The appendix studies ridge regularization r for DCCA on CUB and reports that ridge regularization does not prevent collapse.
- ablation (Figure 8): The appendix studies NR-DCCA regularization weight alpha on CUB and states that too-large alpha slows convergence while too-small alpha leaves collapse.
- result (Tables 2 and 3): Final-epoch tables report NR-DCCA and NR-DGCCA values for synthetic common rates and real-world F1 scores.
- result (Figures 10-12): DGCCA extension results report that noise regularization also helps DGCCA prevent model collapse.

GLOBAL INDEX
Claims:
- [s1] DCCA-based methods exhibit model collapse, with performance dropping drastically as training proceeds.
- [s1] The full-rank property of CCA transformations is claimed to be key to preventing model collapse.
- [s2] The paper states that DCCA-based model collapse has not previously been explored and addressed.
- [s3] The paper states that full-rank DCCA representations alone do not prevent collapse.
- [s4] Correlation between data and Gaussian noise is invariant under full-rank square CCA transformations.
- [s6] Noise regularization is claimed to generalize to DGCCA and potentially other DCCA-based methods.
Method components:
- [s3] MVRL transformation maps multiple views into a unified representation.
- [s3] CCA maximizes pairwise correlations between linearly transformed views.
- [s3] DCCA replaces CCA linear transformations with neural networks.
- [s4] NR-DCCA generates Gaussian white noise for each view during training.
- [s4] NR loss penalizes changes in data-noise correlation before versus after neural transformation.
- [s4] The neural network “full-rank” property is defined by zero NR loss.
Datasets:
- [s5] Synthetic datasets generated from a latent God Embedding with common rates 0%, 20%, 40%, 60%, 80%, and 100%.
- [s5] PolyMnist real-world dataset with varying numbers of views.
- [s5] CUB dataset with visual and text features for bird classification.
- [s5] Caltech101 dataset with HOG, GIST, and SIFT feature views.
- [s7] Synthetic setup uses 4000 samples, 100 latent dimensions, and 50 regression tasks.
Baselines:
- [s5] CONCAT.
- [s5] CCA, PRCCA, and KCCA.
- [s5] DCCA and DGCCA.
- [s5] DCCAE/DGCCAE.
- [s5] DCCA PRIVATE/DGCCA PRIVATE.
- [s5] MVTCAE.
Ablations:
- [s7] Ridge regularization parameter r is varied for DCCA on CUB.
- [s7] Noise regularization weight alpha is varied for NR-DCCA on CUB.
- [s7] DGCCA versus NR-DGCCA experiments test applying the same noise regularization to DGCCA.
Metrics:
- [s5] R2 score for downstream regression with Ridge Regression.
- [s5] Average F1 score for downstream classification with Support Vector Classifier.
- [s5] 5-fold cross-validation averages are reported.
- [s5] Correlation between noise and real data after transformation is used to diagnose collapse.
Results:
- [s3] DCCA transformed unrelated data can show increasing correlation during collapse.
- [s5] On synthetic datasets, NR-DCCA maintains stable performance while DCCA-based baselines collapse during training.
- [s5] On synthetic datasets, methods generally improve as common rate increases.
- [s5] On real-world datasets, NR-DCCA is reported to have stable performance across PolyMnist, CUB, and Caltech101.
- [s7] Final-epoch synthetic and real-world results are tabulated in Tables 2 and 3.
- [s7] NR-DGCCA experiments report that noise regularization helps DGCCA prevent collapse.
Stated limitations:
- [s6] Future work includes exploring noise regularization in contrastive learning and generative models.
- [s6] Future work includes further studying the proposed “full-rank” neural-network definition.
- [s6] Future work includes comparing the proposed regularization concept with orthogonalization and weight decay.
- [s6] The paper states that identifying what neural-network quantities are regularized by noise is interesting but challenging.
```

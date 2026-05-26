# Paper Map

```text
PAPER MAP
Title: R-EDL: Relaxing Nonessential Settings of Evidential Deep Learning
Authors: Mengyuan Chen, Junyu Gao, Changsheng Xu
Venue: ICLR 2024
Submission date: 2023-09-16

SECTIONS
[s1] Abstract and Introduction
Summary: The paper introduces R-EDL, a relaxed version of Evidential Deep Learning for single-forward-pass uncertainty estimation. It argues that traditional EDL fixes a prior weight and includes a variance-minimizing term that are not required by subjective logic, and proposes relaxing both settings to improve uncertainty estimation.
Key items:
- problem: Modern supervised DNN classifiers are described as poorly calibrated and often over-confident, while many Bayesian and ensemble uncertainty methods require multiple forward passes.
- claim: Traditional EDL retains nonessential settings in Dirichlet construction and optimization that can worsen over-confidence.
- method_component: R-EDL treats the prior weight as an adjustable hyperparameter rather than fixing it to the number of classes.
- method_component: R-EDL directly optimizes the expectation/projected probability of the Dirichlet distribution and omits the variance-minimized regularization term.
- result: The paper reports experiments on confidence estimation and OOD detection under classical, few-shot, noisy, and video-modality settings.

[s2] Subjective Logic Theory
Summary: This section defines subjective opinions, projected probability, and the relationship between subjective opinions and Dirichlet probability density functions. It states a theorem giving a bijection between subjective opinions and Dirichlet PDFs when the base rate and prior weight are given.
Key items:
- method_component: A subjective opinion is defined as belief mass, uncertainty mass, and base rate satisfying additivity constraints.
- method_component: Projected probability reallocates uncertainty mass according to the base rate: P_X(x)=b_X(x)+a_X(x)u_X.
- claim (Theorem 1): Given base rate and prior weight W, subjective logic provides a bijection between multinomial opinions and Dirichlet PDFs.
- method_component (Equation 4): The Dirichlet concentration parameter satisfies alpha_X(x)=b_X(x)W/u_X+a_X(x)W.

[s3] R-EDL: Alleviating Over-confidence by Relaxing Nonessential Settings of EDL
Summary: This section reviews traditional EDL and presents the two relaxations used by R-EDL. It analyzes the role of the prior weight in balancing evidence proportion and evidence magnitude, then defines the R-EDL objective that removes the variance-minimized term from the EDL loss.
Key items:
- method_component (Section 3.1): Traditional EDL computes evidence with a neural network and non-negative activation, sets alpha_X(x)=e_X(x)+1 under uniform base rate, and uses projected probability and uncertainty mass for inference.
- claim (Section 3.2): Fixing prior weight W to the class number can produce counter-intuitive projected probabilities in large-class settings.
- method_component (Equation 9): R-EDL generalizes the Dirichlet concentration parameter as alpha_X(x)=e_X(x)+lambda, where lambda=W/C is a hyperparameter.
- method_component (Equation 11): The R-EDL loss minimizes squared error between the one-hot label and projected probability P_X.
- claim (Equation 13): The traditional EDL loss equals squared error on the Dirichlet expectation plus a variance-minimized regularization term.
- method_component (Appendix A.2): The method also adopts a KL-divergence based regularization following prior EDL works.

[s4] Related Work
Summary: This section situates R-EDL among EDL extensions and other single-model uncertainty estimation methods. It discusses DER, I-EDL, DEAR, DUQ, SNGP, prior-network methods, Bayesian neural networks, MC Dropout, and efficient ensemble approaches.
Key items:
- baseline: EDL-related methods discussed include traditional EDL, Deep Evidential Regression, Evidential Tuning Process, I-EDL, and DEAR.
- baseline: Other uncertainty methods discussed include MC Dropout, DUQ, SNGP, Bayesian neural networks, efficient ensembles, KL-PN, RKL-PN, and Posterior Network.
- claim: The paper states that R-EDL is the first method to relax nonessential settings of traditional EDL while adhering to subjective logic.

[s5] Experiments
Summary: The experiments evaluate R-EDL on classification accuracy, confidence estimation, and OOD detection across classical image classification, few-shot learning, noisy data, and video open-set action recognition. The main comparisons are against Dirichlet-based uncertainty methods and selected single-forward-pass or Bayesian uncertainty baselines.
Key items:
- baseline (Section 5.1): Classical image baselines include EDL, I-EDL, KL-PN, RKL-PN, PostN, DUQ, and MC Dropout.
- dataset (Table 1): Classical setting uses MNIST with KMNIST/FMNNIST as OOD data and CIFAR-10 with SVHN/CIFAR-100 as OOD data.
- metric (Section 5.2): Metrics include classification accuracy and AUPR for confidence estimation and OOD detection, using max probability and uncertainty mass as confidence scores for Dirichlet-based methods.
- result (Table 1): In the classical setting, R-EDL reports 99.33% MNIST accuracy and 90.09% CIFAR-10 accuracy, and improves CIFAR-10 to SVHN OOD AUPR over EDL and I-EDL when measured by max probability.
- result (Table 2): In few-shot mini-ImageNet with CUB as OOD data, R-EDL reports strong AUPR scores across 5-way/10-way and 1/5/20-shot tasks, including 83.65 MP OOD AUPR for 5-way 5-shot.
- result (Figure 1(a)): In noisy CIFAR-10 experiments, R-EDL is reported to have better average classification/OOD performance trends across Gaussian noise levels.

[s6] Ablation Study and Parameter Analysis
Summary: This section evaluates the impact of the two R-EDL relaxations: treating lambda as a hyperparameter and removing the variance-minimized regularization term. It also analyzes sensitivity to lambda on CIFAR-10 classification and CIFAR-100 OOD detection.
Key items:
- ablation (Table 3): R-EDL with lambda fixed to 1 tests retaining the original traditional EDL prior-weight setting.
- ablation (Table 3): R-EDL with L_var tests reintroducing the deprecated variance-minimized regularization term.
- result (Table 3): On CIFAR-10 to SVHN OOD detection, R-EDL reports 85.00 AUPR, compared with 83.24 for lambda=1 and 84.04 with L_var.
- result (Table 3): On 10-way 5-shot mini-ImageNet to CUB OOD detection, R-EDL reports 83.37 AUPR, compared with 82.89 for lambda=1 and 82.25 with L_var.
- metric (Figure 1(b)): Parameter analysis varies lambda from 0.01 to 1.5 and reports CIFAR-10 accuracy and CIFAR-100 OOD AUPR.
- method_component: For the CIFAR-10 setting, lambda is selected as 0.1 from [0.1:0.1:1.0] based on validation classification accuracy.

[s7] Conclusion
Summary: The paper concludes that R-EDL relaxes two traditional EDL settings in model construction and optimization. It identifies future directions concerning the optimal prior-weight mechanism and richer optimization goals for Dirichlet PDFs.
Key items:
- claim: The paper summarizes that prior weight controls the balance between evidence proportion and evidence magnitude in predictive scores.
- claim: The paper summarizes that the variance-minimized term drives the Dirichlet PDF toward a Dirac-delta-like distribution and can heighten over-confidence risk.
- stated_limitation: The mechanism determining the optimal prior weight value remains for further investigation.
- stated_limitation: The R-EDL objective optimizes the expected value of the Dirichlet PDF and is described as somewhat coarse; future work could consider other statistical properties.

[s8] Appendices
Summary: The appendices provide proofs, derivations, dataset details, implementation details, additional results, visualizations, and the source code link. They include derivations for uncertainty measures such as expected entropy, mutual information, and differential entropy, and additional experiments on classical, few-shot, noisy, and video settings.
Key items:
- method_component (Appendix A.1): Proof of the bijection between subjective opinions and Dirichlet PDFs is provided.
- method_component (Appendix A.2): Derivations of EDL optimization objectives and KL regularization are provided.
- metric (Appendix B): Expected entropy, mutual information, and differential entropy are derived as Dirichlet-based uncertainty measures.
- dataset (Appendix C.1): Dataset details include MNIST, FMNIST, KMNIST, CIFAR-10, SVHN, CIFAR-100, mini-ImageNet, CUB, UCF-101, HMDB-51, and MiT-v2.
- result (Table 12): Video-modality results report R-EDL scores of 78.73 open maF1 and 77.94 open-set AUC for UCF-101 to HMDB-51, and 70.85 open maF1 and 82.26 open-set AUC for UCF-101 to MiT-v2.
- other (Appendix E): Source code is linked at https://github.com/MengyuanChen21/ICLR2024-REDL.

GLOBAL INDEX
Claims:
- [s1] Traditional EDL has nonessential settings in model construction and optimization that can exacerbate over-confidence.
- [s2] Subjective logic gives a bijection between subjective opinions and Dirichlet PDFs when base rate and prior weight are given.
- [s3] The prior weight governs the balance between using evidence proportion and evidence magnitude in projected probabilities.
- [s3] The variance-minimized term in traditional EDL encourages the Dirichlet PDF toward a Dirac delta function.
- [s4] R-EDL is presented as relaxing traditional EDL settings while remaining within subjective logic.
- [s7] R-EDL relaxations are claimed to alleviate over-confidence and improve uncertainty estimation.
Method components:
- [s2] Subjective opinion components: belief mass, uncertainty mass, and base rate.
- [s2] Projected probability: P_X(x)=b_X(x)+a_X(x)u_X.
- [s3] Evidence vector e_X=f(g(z)) with non-negative activation such as Softplus.
- [s3] Generalized Dirichlet concentration parameter alpha_X(x)=e_X(x)+lambda.
- [s3] R-EDL loss directly minimizes MSE between one-hot labels and projected probabilities.
- [s3] KL-divergence regularization suppresses evidence for non-target classes.
Datasets:
- [s5] MNIST as ID data with KMNIST and FMNIST as OOD data.
- [s5] CIFAR-10 as ID data with SVHN and CIFAR-100 as OOD data.
- [s5] mini-ImageNet few-shot episodes with CUB as OOD data.
- [s8] UCF-101 as ID data with HMDB-51 and MiT-v2 as OOD data for video open-set action recognition.
Baselines:
- [s5] EDL, I-EDL, KL-PN, RKL-PN, PostN, DUQ, and MC Dropout for image experiments.
- [s5] OpenMax, MC Dropout, BNN SVI, RPL, and DEAR for video-modality experiments.
- [s8] Temperature scaling is compared in additional classical-setting calibration results.
Ablations:
- [s6] R-EDL with lambda=1 restores the original prior-weight setting.
- [s6] R-EDL with L_var reintroduces the variance-minimized regularization term.
- [s6] Restoring both original settings corresponds to traditional EDL.
- [s6] Parameter analysis varies lambda from 0.01 to 1.5.
Metrics:
- [s5] Classification accuracy.
- [s5] AUPR for confidence estimation and OOD detection.
- [s5] Max probability and uncertainty mass as confidence scores for Dirichlet-based methods.
- [s8] AUROC, expected calibration error, Brier score, differential entropy, mutual information, and expected entropy in appendices.
- [s8] Open maF1 and open-set AUC for video open-set action recognition.
Results:
- [s5] R-EDL reports 99.33% MNIST classification accuracy and 90.09% CIFAR-10 classification accuracy in the classical setting.
- [s5] R-EDL reports improved CIFAR-10 to SVHN OOD AUPR compared with EDL and I-EDL when measured by max probability.
- [s5] R-EDL reports 83.65 MP OOD AUPR on 5-way 5-shot mini-ImageNet to CUB.
- [s6] Ablations show lower OOD AUPR when lambda is fixed to 1 or L_var is reintroduced.
- [s8] Video results report R-EDL outperforming listed baselines on UCF-101 to HMDB-51 and MiT-v2 in Table 12.
Stated limitations:
- [s7] The mechanism dictating the optimal prior weight value is left for further investigation.
- [s7] The current objective optimizes the Dirichlet expected value and is described as somewhat coarse.
- [s7] Future work could explore objectives using other statistical properties of Dirichlet PDFs.
```

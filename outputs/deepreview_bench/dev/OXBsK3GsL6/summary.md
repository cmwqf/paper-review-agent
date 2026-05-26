# Paper Map

```text
PAPER MAP
Title: Soft iEP: On the Exploration Inefficacy of Gradient Based Strong Lottery Exploration
Authors: Anonymous authors
Venue: ICLR 2024
Submission date: 2023-09-22

SECTIONS
[s1] Introduction
Summary: This section introduces strong lottery tickets and the Edge-Popup algorithm used to find sparse subnetworks without weight updates. It identifies dying edges as edges never selected during EP optimization and proposes Soft iterative Edge-Popup as a remedy. It summarizes empirical claims on ImageNet, CIFAR-10, and CIFAR-100.
Key items:
- problem (Figure 1): EP may be trapped near randomly selected initial subnetworks because many edges are never selected during search.
- method_component (Figure 1): Dying edges are defined as masked edges that have never been activated during optimization.
- claim: Soft iEP repeatedly applies EP with gradually increasing pruning while not permanently disabling bottom edges from earlier cycles.
- dataset: Empirical validation uses ImageNet, CIFAR-10, and CIFAR-100.
- result: Soft iEP is stated to outperform EP and hard iEP across tested datasets and model sizes.
- result: With WideResNet-50 search space, Soft iEP reports 76.0% ImageNet accuracy with about 20M parameters.

[s2] Background
Summary: This section defines the Strong Lottery Ticket Hypothesis and contrasts it with the standard Lottery Ticket Hypothesis. It reviews iterative pruning and rewinding in LTH and describes the EP optimization procedure for finding SLTs.
Key items:
- method_component (Definition 2.1): SLTH states that a randomly initialized dense network contains a sparse mask that reaches comparable accuracy without weight training.
- method_component: EP assigns a real-valued score to each edge and selects each layer's top-scored edges under a pruning ratio.
- method_component (Equation 1): EP optimizes scores using SGD and a straight-through estimator while keeping initial weights fixed.
- method_component: The paper mainly samples weights from a signed Kaiming constant distribution following prior EP work.
- other: Prior SLT evidence includes theoretical work on existence and empirical work on classification and generative models.

[s3] Exploration Inefficiency of EP
Summary: This section formalizes the dying ratio and distinguishes true negative from false negative dying edges. It reports case studies measuring dying ratios for EP on CIFAR-10, SVHN, Conv8, and ResNet18 under different pruning and initialization settings.
Key items:
- metric (Equation 2): Dying ratio d_t is the fraction of edges never selected up to iteration t; k minus d_T measures initially masked edges selected at least once.
- method_component (Figure 2): The paper distinguishes true negative dying edges from false negative dying edges that should have been selected.
- dataset (Table 1, Table 2): Case study applies EP to ResNet18 on CIFAR-10 and SVHN, with additional initialization tests on Conv8 and ResNet18.
- result (Table 1): For CIFAR-10 ResNet18, d_T increases from 0.028 at pruning k=0.200 to 0.656 at k=0.832.
- result (Table 1): For CIFAR-10 ResNet18, k minus d_T is around 0.20 across tested pruning ratios.
- ablation (Table 2): Score and weight initialization variants affect dying ratio and test accuracy; the default setting is reported as best or on par in most cases.

[s4] Proposal: Soft Iterative Edge Popup
Summary: This section introduces iterative EP with hard pruning and then Soft iEP. Hard iEP permanently restricts later search to masks retained from earlier cycles, while Soft iEP increases pruning over cycles but keeps the full initial search space available.
Key items:
- method_component (Section 4.1): Hard iEP iteratively prunes by shrinkage rate p and searches within the previously retained mask.
- method_component (Table 3): Four hard iEP variants are defined: fine-tuning, score rewinding, score reinitializing, and learning-rate rewinding.
- problem (Section 4.2): Hard pruning can permanently remove edges early, creating possible false negative dying edges.
- method_component (Table 3): Soft iEP inherits prior-cycle scores, resets the learning rate by default, raises the pruning ratio over cycles, and keeps search space as the original theta_0.
- ablation (Table 3): Soft pruning with zero initialization of pruned scores is compared and stated to induce dying edges and hurt performance.
- claim: The paper states that learned score initialization in Soft iEP helps reduce dying edges compared with random score initialization in EP.

[s5] Experiments
Summary: This section evaluates EP, hard iEP, Soft iEP, IteRand, dense trained networks, multicoated tickets, and architecture variants. Experiments cover ImageNet, CIFAR-10, and CIFAR-100, with additional analyses of dying ratios and score-rank transitions.
Key items:
- dataset (Figure 3): ImageNet experiments use ResNet-50, ResNet-101, WideResNet-50 for SLT search and ResNet-18/34 dense training comparisons.
- baseline (Figure 3, Figure 4): Baselines include EP, hard iEP, IteRand, dense weight training, multicoated lottery tickets, and hard iEP rewinding variants.
- metric (Figure 3, Figure 5): Reported metrics include test accuracy, parameter count, remaining ratio, and dying ratio.
- result (Figure 3(a)): On ImageNet, Soft iEP with WideResNet-50 reports 76.0% accuracy with about 20M parameters, about 2.7 points above EP and dense training at similar parameter count.
- result (Figure 3(b)): On CIFAR-10 and CIFAR-100 with ResNet18, iterative pruning improves maximum test accuracy over one-shot EP by 1.33 and 1.84 points, respectively.
- result (Figure 5(a)): Soft iEP reduces dying ratio in most regions and shows near-zero dying ratio in early cycles.

[s6] Conclusion and Limitation
Summary: This section restates the paper's analysis of EP through dying ratio, its testing of iterative pruning variants for SLT, and its proposal of soft pruning. It also lists increased search time and missing theoretical analysis as limitations.
Key items:
- claim: Dying ratio is presented as a measure of exploration inefficacy in finding strong lottery ticket structures.
- claim: The paper states that testing iterative pruning variants in SLT provides a methodological connection between LT and SLT.
- result: Soft iEP is summarized as reducing dying edges and outperforming EP, hard iEP, and IteRand in the reported experiments.
- stated_limitation: Soft iEP increases search time because EP is applied iteratively.
- stated_limitation: Theoretical investigation of why dying edges occur and why soft pruning succeeds is left for future work.
- stated_limitation: The paper notes an open question about why original EP can work despite high dying ratios.

GLOBAL INDEX
Claims:
- [s1] EP can induce many dying edges and search only near randomly selected initial subnetworks.
- [s1] Soft iEP is claimed to outperform EP and hard iEP on ImageNet, CIFAR-10, and CIFAR-100.
- [s4] Soft pruning avoids permanently disabling bottom edges from earlier cycles.
- [s4] Learned score initialization is claimed to reduce dying edges relative to random score initialization.
- [s6] Dying ratio is proposed as an empirical lens for exploration inefficacy in EP.
Method components:
- [s2] Strong Lottery Ticket Hypothesis and fixed-weight masked subnetworks.
- [s2] Edge-Popup score optimization with top-score masks and straight-through estimator.
- [s3] Dying edge and dying ratio definition.
- [s4] Hard iterative Edge-Popup with shrinkage rate p and retained mask search space.
- [s4] Soft iterative Edge-Popup with increasing pruning ratio, inherited scores, learning-rate rewinding, and full search space.
- [s4] Rewinding variants: FT, SRw, SRi, and LR.
Datasets:
- [s3] CIFAR-10 and SVHN for EP dying-ratio case study.
- [s5] ImageNet for large-scale classification experiments.
- [s5] CIFAR-10 and CIFAR-100 for ResNet18 and architecture-variant experiments.
Baselines:
- [s5] Standard Edge-Popup.
- [s5] Hard iEP with fine-tuning, score rewinding, score reinitializing, and learning-rate rewinding.
- [s5] IteRand.
- [s5] Dense networks trained with standard gradient descent.
- [s5] Multicoated lottery tickets.
Ablations:
- [s3] Score and weight initialization choices for EP are compared for accuracy and dying ratio.
- [s4] Hard iEP rewinding choices are compared in Table 3 and CIFAR experiments.
- [s4] Soft pruning with zero initialization is compared as a variant.
- [s5] Soft iEP is evaluated across backbone choices including ResNet18x2, ResNeXt, and ConvMixer.
- [s5] Soft iEP is combined with multicoated tickets.
Metrics:
- [s3] Dying ratio d_t.
- [s3] k minus d_T, the percentage of initially masked edges selected at least once.
- [s5] Test accuracy.
- [s5] Remaining ratio and parameter count.
Results:
- [s3] For CIFAR-10 ResNet18, EP dying ratio rises from 0.028 at k=0.200 to 0.656 at k=0.832.
- [s3] For CIFAR-10 ResNet18, k minus d_T is approximately 0.20 over tested pruning ratios.
- [s5] Soft iEP with WideResNet-50 reaches 76.0% ImageNet accuracy with about 20M parameters.
- [s5] The paper reports Soft iEP generally outperforms EP, hard iEP, IteRand, and dense networks across ImageNet model sizes tested.
- [s5] On CIFAR-10 and CIFAR-100 with ResNet18, iterative pruning improves maximum test accuracy over one-shot EP by 1.33 and 1.84 points.
- [s5] Soft iEP reduces dying ratio in most tested regions and has near-zero dying ratio in early cycles.
Stated limitations:
- [s6] The method increases search time because EP is applied iteratively.
- [s6] Theoretical explanation of dying edges and soft pruning success is not provided.
- [s6] The relationship between dying edges and prior SLT theory is left for future investigation.
- [s6] The paper identifies as open why original EP works sufficiently well despite high dying ratios.
```

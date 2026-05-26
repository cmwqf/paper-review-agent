# Paper Map

```text
PAPER MAP
Title: Revisiting Plasticity in Visual Reinforcement Learning: Data, Modules and Training Stages
Authors: Guozheng Ma, Lu Li, Sen Zhang, Zixuan Liu, Zhen Wang, Yixin Chen, Li Shen, Xueqian Wang, Dacheng Tao
Venue: ICLR 2024
Submission date: 2023-10-11

SECTIONS
[s1] Introduction
Summary: The paper frames plasticity loss as a central obstacle for sample-efficient visual reinforcement learning. It states three empirical findings about data augmentation, critic plasticity, and early-stage intervention, and proposes Adaptive Replay Ratio as a method motivated by these findings.
Key items:
- problem: Visual RL agents must learn from non-stationary data and objectives, making plasticity loss a sample-efficiency challenge.
- claim: Data augmentation is indispensable for preserving plasticity in visual RL agents.
- claim: The critic module's plasticity loss is identified as the main bottleneck for efficient training.
- claim: Early-stage plasticity recovery is necessary; without timely intervention, critic plasticity loss becomes catastrophic.
- method_component: Adaptive RR dynamically changes replay ratio based on the critic's plasticity level.

[s2] Related Work
Summary: This section reviews prior work on plasticity loss in reinforcement learning and on the high replay-ratio dilemma. It contrasts reset-based, regularization-based, and architecture-based plasticity interventions, and describes replay ratio as the number of updates per environment step.
Key items:
- problem: Plasticity loss has been discussed under terms including primacy bias, dormant neurons, implicit underparameterization, capacity loss, and plasticity loss.
- baseline: Prior interventions include Reset, ReDo, Plasticity Injection, L2-Init, and Concatenated ReLU.
- problem: Increasing replay ratio can improve data reuse but can also intensify plasticity loss.
- claim: The paper positions Adaptive RR as a dynamic replay-ratio approach based on critic plasticity.

[s3] Data: Data Augmentation Is Essential in Maintaining Plasticity
Summary: This section studies data augmentation through factorial experiments with Reset and comparisons against other interventions. The reported experiments use DrQ-v2 on DeepMind Control tasks and show that data augmentation alone preserves plasticity more effectively than Reset without augmentation.
Key items:
- ablation (Figure 1): Factorial experiment compares four combinations: with or without data augmentation and with or without Reset.
- result (Figure 1): Without data augmentation, Reset consistently improves performance, indicating plasticity loss.
- result (Figure 1): With data augmentation, adding Reset gives only slight improvement or sometimes decreases performance.
- baseline: Architectural and optimization interventions include Weight Decay, L2-Init, Layer Normalization, Spectral Normalization, Shrink and Perturb, and CReLU.
- result (Figure 2): Data augmentation is reported as the most effective intervention among the compared methods on Cheetah Run.

[s4] Modules: The Plasticity Loss of Critic Network Is Predominant
Summary: This section separates the visual RL agent into encoder, actor, and critic modules and measures their plasticity trends. Experiments with FAU, a frozen ImageNet-pretrained encoder, and plasticity injection support the paper's claim that critic plasticity loss dominates sample inefficiency.
Key items:
- metric (Equation 1): Fraction of Active Units measures the proportion of neurons with positive activation in a module.
- result (Figure 3): Data augmentation substantially raises critic FAU, while encoder and actor FAU show similar trends with or without augmentation.
- ablation (Figure 4): Uses a frozen ImageNet-pretrained ResNet encoder to isolate representation learning effects.
- result (Figure 4): With a frozen pretrained encoder, using data augmentation still outperforms not using it.
- ablation (Figure 5): Plasticity injection is applied separately to actor and critic, with and without data augmentation.
- result (Figure 5): Without data augmentation during early training, plasticity injection into the critic significantly improves performance.

[s5] Stages: Early-Stage Plasticity Loss Becomes Irrecoverable
Summary: This section studies how plasticity loss differs across training stages by turning data augmentation on or off at selected training steps. It reports that early critic plasticity recovery is crucial, while later plasticity decline may be benign in single-task visual RL.
Key items:
- ablation (Figure 6): Data augmentation is turned on or off at particular training steps to test early and late intervention effects.
- result (Figure 6): Turning off data augmentation after critic plasticity recovery does not affect training efficiency.
- result (Figure 6): Turning on data augmentation after significant early plasticity loss does not revive training performance.
- claim: The paper distinguishes early catastrophic plasticity loss from later benign plasticity loss.
- motivation: Early bootstrapped targets are described as highly non-stationary because they are based on limited and low-quality experience.

[s6] Methods: Adaptive RR for Addressing the High RR Dilemma
Summary: This section introduces Adaptive RR, which starts with a low replay ratio and switches to a higher replay ratio when critic FAU stabilizes. Evaluations on DeepMind Control and Atari-100K compare Adaptive RR against static replay-ratio settings and reset-based methods.
Key items:
- problem (Figure 7): Higher static replay ratio can reduce sample efficiency because early plasticity loss becomes more severe.
- metric (Figure 8): Critic FAU is used to monitor plasticity and decide when to increase replay ratio.
- method_component: Adaptive RR starts at RR=0.5 and switches to RR=2 when consecutive critic FAU checkpoints differ by less than 0.001.
- dataset (Figure 9): DeepMind Control evaluation uses six challenging continuous-control tasks.
- result (Figure 9): Adaptive RR shows higher sample efficiency than static low RR and static high RR on the reported DMC tasks.
- result (Table 2): On Atari-100K, Adaptive RR obtains mean HNS 55.8%, median HNS 48.7%, 4 superhuman games, and 11 best scores among compared settings.

[s7] Conclusion, Limitations, and Future Work
Summary: The conclusion restates the three main findings and the Adaptive RR proposal. The limitations name the experimental scope and the basic design of Adaptive RR, while future work calls for further study of DRL-specific architectures and optimization techniques.
Key items:
- claim: Data augmentation mitigates plasticity loss; critic plasticity is the primary hurdle; early recovery is pivotal for efficient training.
- stated_limitation: Experiments focus on DeepMind Control and Atari environments, without evaluation in more complex settings.
- stated_limitation: Adaptive RR is demonstrated only under basic configurations.
- other: The authors suggest future work on DRL-specific network architectures and optimization techniques.

[s8] Appendices and Experimental Details
Summary: The appendices provide extended related work, additional experiments, the Adaptive RR algorithm, and hyperparameters for DMC and Atari. Additional figures cover Reset intervals, heavy priming, intervention comparisons, plasticity-injection replications, FAU trends, and extra plasticity metrics.
Key items:
- method_component (Algorithm 1): Adaptive RR algorithm checks critic FAU every interval and switches to high RR when the FAU change is below a threshold.
- dataset (Table 3): DMC experiments use image observations and DrQ-v2 hyperparameters including replay buffer capacity 1e6, batch size 256, learning rate 1e-4, and hidden dimension 1024.
- dataset (Table 5): Atari-100K experiments use the Dopamine framework, 17 games, and 5 random seeds per game.
- metric (Appendix B.7): Additional plasticity metrics discussed include feature rank, weight norm, and FAU.
- result (Appendix B): Additional DMC and Atari tables and figures report consistent trends for Reset, plasticity injection, DA timing, and FAU across tasks and seeds.

GLOBAL INDEX
Claims:
- [s1] Data augmentation is essential for maintaining plasticity in visual reinforcement learning.
- [s1] The critic module's plasticity loss is the main bottleneck for efficient visual RL training.
- [s5] Plasticity loss in early training can become catastrophic and irrecoverable if not addressed promptly.
- [s6] Adaptive RR can balance data reuse and plasticity loss by changing replay ratio based on critic FAU.
Method components:
- [s3] Data augmentation applied to input observations in DrQ-v2-style visual RL.
- [s4] FAU-based module analysis for encoder, actor, and critic.
- [s4] Plasticity injection applied separately to actor and critic as a diagnostic tool.
- [s6] Adaptive RR starts with low RR and switches to high RR after critic FAU stabilizes.
- [s8] Algorithm 1 specifies the check interval, FAU threshold, and switch rule for Adaptive RR.
Datasets:
- [s6] DeepMind Control suite continuous-control visual RL tasks.
- [s6] Atari-100K benchmark with 17 games.
- [s4] ImageNet-pretrained ResNet encoder used in frozen-encoder experiments.
Baselines:
- [s3] DrQ-v2 with and without data augmentation.
- [s3] Reset, Weight Decay, L2-Init, Layer Normalization, Spectral Normalization, Shrink and Perturb, and CReLU.
- [s6] Static RR=0.5 and static RR=2 on DMC.
- [s6] Static RR settings and ReDo on Atari-100K.
- [s6] Reset and ReDo under static replay-ratio settings.
Ablations:
- [s3] Four-way comparison of data augmentation and Reset presence or absence.
- [s4] Frozen ImageNet-pretrained encoder comparison with and without data augmentation.
- [s4] Plasticity injection into actor versus critic, with and without data augmentation.
- [s5] Turning data augmentation on or off at selected training steps.
- [s6] Varying static replay ratio values and comparing them to Adaptive RR.
Metrics:
- [s4] Fraction of Active Units for encoder, actor, and critic plasticity.
- [s6] Average episode return on DMC tasks.
- [s6] Human-normalized score, median HNS, number of superhuman games, and number of best scores on Atari-100K.
- [s8] Feature rank and weight norm are discussed as additional plasticity metrics.
Results:
- [s3] Reset improves training in the absence of data augmentation, while adding Reset to data augmentation gives limited or negative gains.
- [s4] Critic FAU changes strongly with data augmentation, while actor and encoder FAU trends are similar across augmentation settings.
- [s4] Plasticity injection into the critic improves performance after no-augmentation early training.
- [s5] Early use of data augmentation enables critic plasticity recovery; late use after severe loss does not recover training performance.
- [s6] Adaptive RR outperforms static low and high replay-ratio settings in the reported DMC learning curves.
- [s6] Adaptive RR reports 55.8% mean HNS and 48.7% median HNS on Atari-100K.
Stated limitations:
- [s7] Experiments are limited to DMC and Atari environments and do not evaluate more complex settings.
- [s7] Adaptive RR is evaluated only under basic configurations, and more nuanced designs are left for future work.
```

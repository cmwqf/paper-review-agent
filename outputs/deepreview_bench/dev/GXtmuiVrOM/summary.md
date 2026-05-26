# Paper Map

```text
PAPER MAP
Title: Domain Randomization via Entropy Maximization
Authors: Gabriele Tiboni, Pascal Klink, Jan Peters, Tatiana Tommasi, Carlo D'Eramo, Georgia Chalvatzaki
Venue: ICLR 2024
Submission date: 2023-11-03

SECTIONS
[s1] Introduction
Summary: This section motivates sim-to-real reinforcement learning under a reality gap and frames dynamics domain randomization as a trade-off between robustness and excessive conservatism. It introduces DORAEMON, which widens the training dynamics distribution by maximizing entropy while maintaining a required task success probability and using no real-world data.
Key items:
- problem: Domain randomization requires choosing a dynamics sampling distribution; too much randomization can over-regularize policies, while too little can fail to generalize.
- claim: DORAEMON automatically shapes the dynamics distribution during simulation training without real-world data.
- method_component: The method maximizes distribution entropy subject to a minimum probability of task success.
- claim: The approach needs only a task success notion, such as a return threshold or a task-specific success indicator.
- claim: The paper claims DORAEMON is more sample efficient than methods that require extra policy evaluations because it updates the distribution using training episodes.
- result: The introduction states successful zero-shot transfer on a 7-DoF robotic arm pushing task with unknown dynamics parameters.

[s2] Related Work
Summary: This section situates the paper among domain randomization, adaptive domain randomization, automated domain randomization without real data, and curriculum learning. It contrasts DORAEMON with methods requiring real-world data, reference distributions, boundary evaluations, or context-conditioned policies.
Key items:
- baseline: LSDR guides a training distribution to maximize average performance over a fixed reference dynamics range.
- baseline: AutoDR expands a uniform distribution using policy performance at distribution boundaries.
- motivation: Prior methods without real data may require repeated Monte Carlo policy evaluations, a reference DR distribution, or boundary-biased samples.
- method_component: The paper connects history-dependent policies in DR to implicit system identification over latent dynamics parameters.
- other: The authors distinguish DORAEMON from self-paced curriculum learning, which usually assumes a target task distribution.

[s3] Background
Summary: This section defines the reinforcement learning and domain randomization setting as a set of MDPs sharing state, action, and reward spaces but differing in transition dynamics. It formulates the expected return under sampled dynamics parameters and motivates history-conditioned policies because dynamics parameters are latent.
Key items:
- method_component (Equation 1): The simulator is modeled as a set of MDPs indexed by latent dynamics parameters ξ sampled from a parametric distribution νφ.
- method_component (Equation 1): Domain randomization optimizes expected discounted return over trajectories generated under ξ sampled from νφ.
- method_component: The policy is not conditioned on ξ, so the paper adopts policies conditioned on histories of prior states and actions.

[s4] Method
Summary: This section defines DORAEMON as a constrained entropy maximization problem over the dynamics distribution and policy. It presents a practical alternating implementation with SAC, history-conditioned actors, asymmetric critics using true dynamics parameters, KL trust regions, importance-sampled success estimates, and a backup optimization for constraint violations.
Key items:
- method_component (Equation 2): A binary success indicator σ maps trajectories to success or failure and defines the success probability G(θ, φ).
- method_component (Equation 3): DORAEMON maximizes entropy H(νφ) subject to G(θ, φ) ≥ α.
- method_component (Equation 4): The practical update maximizes next-distribution entropy with both a success constraint and a KL trust-region constraint to the current distribution.
- method_component (Equation 5): The success probability under a proposed distribution is approximated by importance sampling from trajectories collected under the current distribution.
- method_component (Equation 6): A backup optimization searches within the trust region for a distribution with maximum estimated in-distribution success rate.
- method_component (Algorithm 1): The implementation uses uncorrelated univariate Beta distributions for dynamics parameters, SAC for policy training, history-conditioned actors, and critics conditioned on true dynamics parameters.

[s5] Toy Problem
Summary: This section illustrates DORAEMON on an inclined-plane cart task where the hidden dynamics parameter is the plane inclination. The example shows how different α values shape the final Beta distribution and how success/failure relates to analytically feasible inclination ranges.
Key items:
- dataset (Section 4.2): Toy inclined-plane cart task with inclination angle ω as the randomized dynamics parameter.
- metric (Section 4.2): A trajectory is considered successful if the cart balances around the center of the plane for at least 25 timesteps.
- result (Figure 1): Figure 1 shows that lower α values yield higher-entropy final distributions while higher α values lead to more conservative entropy.
- result (Figure 1): The toy results report that policies solve the task across the feasible parameter range ω ∈ [-ωc, ωc].

[s6] Experiments
Summary: This section evaluates DORAEMON on MuJoCo sim-to-sim benchmarks and a PandaPush sim-to-real robotic manipulation task. It compares against No-DR, Fixed-DR, LSDR, and AutoDR using success rates, entropy, returns, and final distances.
Key items:
- baseline (Section 5.1): Baselines are No-DR, Fixed-DR with maximum-entropy uniform distribution, LSDR, and AutoDR.
- dataset (Section 5.2): Sim-to-sim evaluation uses six OpenAI Gym MuJoCo tasks with randomized dynamics parameters and return-threshold success definitions.
- metric (Section 5.2): Global Success Rate is measured over the maximum-entropy uniform distribution νmax.
- result (Figure 2): Figure 2 reports higher and/or faster convergence of DORAEMON across the sim-to-sim tasks compared with baselines.
- dataset (Section 5.3): PandaPush is a 7-DoF Franka Panda pushing task with 17 randomized dynamics parameters including box mass, surface friction, joint damping/friction, and center of mass.
- result (Table 1): On PandaPush, DORAEMON reports 66.57% Sim2Sim success and 60% Sim2Real success, compared with 37.77% and 46.67% for LSDR and 30.45% and 26.67% for AutoDR.

[s7] Appendices and Conclusion
Summary: The appendices provide environment parameter ranges, hyperparameters, additional analyses, ablations, distribution-family comparisons, curriculum-learning connections, and PandaPush details. The conclusion summarizes DORAEMON and states limitations concerning backtracking behavior, catastrophic forgetting, and possible use of prior dynamics knowledge.
Key items:
- dataset (Table 2): Appendix A lists randomized parameters, boundaries, and return thresholds for CartPole, SwingUpCartpole, Hopper, Walker2D, HalfCheetah, and Swimmer.
- ablation (Figure 13): Appendix B ablates DORAEMON components relative to SPDL, including history, asymmetric critic, oracle dynamics conditioning, and backup optimization.
- ablation (Figure 11): Appendix A compares Beta and Gaussian parameterizations of the DORAEMON dynamics distribution.
- metric (Appendix C): PandaPush success is defined as the box ending within 3 cm of the goal.
- stated_limitation: DORAEMON may collapse to an easy region of the optimization landscape when backtracking from the current distribution.
- stated_limitation: If prior knowledge of the dynamics is available, biasing distribution growth around it may be beneficial but harder to optimize.

GLOBAL INDEX
Claims:
- [s1] DORAEMON automatically shapes simulator dynamics distributions during training without real-world data.
- [s1] Maximizing entropy while constraining success is claimed to produce adaptive, generalizable policies over wide dynamics ranges.
- [s1] The method is claimed to be sample efficient because distribution updates use trajectories already collected during training.
- [s6] The paper reports DORAEMON outperforms No-DR, Fixed-DR, LSDR, and AutoDR on the evaluated sim-to-sim and PandaPush settings.
Method components:
- [s3] Domain randomization is modeled as sampling latent dynamics parameters ξ from νφ over a set of MDPs.
- [s3] Policies are conditioned on histories of state-action information because ξ is latent.
- [s4] Success indicator σ(τ) defines probability of success G(θ, φ).
- [s4] DORAEMON solves entropy maximization subject to minimum success rate α.
- [s4] Distribution updates include a KL trust-region constraint between consecutive dynamics distributions.
- [s4] Importance sampling estimates success for proposed distributions using current training data.
- [s4] Backup optimization backtracks to a nearby distribution with high estimated success when constraints are violated.
- [s4] Implementation uses SAC, history-conditioned policy, and an asymmetric critic conditioned on true dynamics parameters.
- ... 1 more
Datasets:
- [s5] Toy inclined-plane cart task with inclination angle as dynamics parameter.
- [s6] OpenAI Gym MuJoCo sim-to-sim benchmark tasks: CartPole, SwingUpCartpole, Hopper, Walker2D, HalfCheetah, and Swimmer.
- [s6] PandaPush 7-DoF Franka Panda robotic pushing task with unknown box center of mass and other randomized dynamics.
- [s7] Appendix tables specify randomized parameter boundaries for MuJoCo tasks and PandaPush.
Baselines:
- [s6] No-DR: policy trained on a single simulator instance with fixed dynamics.
- [s6] Fixed-DR: policy trained with a fixed maximum-entropy uniform dynamics distribution.
- [s6] LSDR: learned domain randomization distribution using a reference distribution.
- [s6] AutoDR: automatic expansion of a uniform distribution based on boundary performance.
- [s7] SPDL-related variants are used in appendix ablations to compare curriculum-learning components.
Ablations:
- [s6] Effect of α on success-rate versus entropy trade-off in Hopper.
- [s6] Effect of success lower-bound threshold JLB on performance versus entropy in Hopper.
- [s7] Trust-region size ε sensitivity analysis for DORAEMON.
- [s7] Beta versus Gaussian distribution parameterization comparison.
- [s7] Ablation of history, asymmetric critic, oracle dynamics-conditioned policy, and backup optimization relative to SPDL.
Metrics:
- [s4] Distribution entropy H(νφ).
- [s4] In-distribution success probability G(θ, φ).
- [s6] Global Success Rate over νmax.
- [s6] Average test return for sim-to-sim tasks.
- [s6] PandaPush success rate and final distance to target in centimeters.
- [s7] PandaPush success threshold: final box position within 3 cm of goal.
Results:
- [s5] In the inclined-plane toy problem, DORAEMON distributions converge to different entropies depending on α and policies solve feasible inclinations.
- [s6] Figure 2 reports DORAEMON with better and/or faster sim-to-sim convergence across all tested MuJoCo tasks.
- [s6] Figure 3 shows DORAEMON solving a wider area of a HalfCheetah two-parameter dynamics slice.
- [s6] DORAEMON outperforms Fixed-DR in Figure 2, including cases where it approaches νmax.
- [s6] For PandaPush, Table 1 reports DORAEMON Sim2Sim success rate of 66.57% and final distance 3.17 ± 3.04 cm.
- [s6] For PandaPush, Table 1 reports DORAEMON Sim2Real success rate of 60% and final distance 2.68 ± 1.01 cm.
- [s7] Appendix results report DORAEMON tracks desired in-distribution success rate α across multiple settings.
Stated limitations:
- [s7] DORAEMON may suffer from collapsing to an easy region of the optimization landscape when backtracking from the current distribution.
- [s7] The authors suggest a KL constraint between the current policy and the best-performing policy could help prevent catastrophic forgetting.
- [s7] If prior dynamics knowledge is available, biasing distribution growth around it may be useful, but the paper states this is a harder optimization problem.
- [s7] Appendix discussion notes that backtracking can sometimes reduce global success because policies may forget previously experienced dynamics.
```

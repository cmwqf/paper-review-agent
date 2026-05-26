# Paper Map

```text
PAPER MAP
Title: 3D Diffuser Actor: Multi-task 3D Robot Manipulation with Iterative Error Feedback
Authors: Anonymous authors
Venue: ICLR 2024
Submission date: 2023-09-21

SECTIONS
[s1] Abstract and Introduction
Summary: The paper introduces 3D Diffuser Actor, a language- and vision-conditioned diffusion policy for predicting robot end-effector keyposes from 3D scene representations. It motivates the method by discussing multimodal demonstrations and the generalization benefits of 3D scene encodings. The paper claims improved performance over prior 3D policies and 2D diffusion policies on RLBench and real-world tasks.
Key items:
- problem: Learning robot manipulation policies from multimodal demonstrations where multiple actions can be task-optimal.
- claim: Combining diffusion policies with 3D scene representations improves multi-task robot manipulation.
- method_component (Figure 1): The model iteratively denoises 3D translations and rotations conditioned on language, RGB-D observations, action history, and proprioception.
- method_component (Figure 1): The current end-effector estimate is grounded in the 3D workspace and featurized with relative 3D attention.
- result: The paper reports a 12 percentage-point absolute gain over the previous state of the art on RLBench.

[s2] Related Work
Summary: This section surveys imitation learning from demonstrations, diffusion models in robotics, and 2D/3D scene representations for robot manipulation. It contrasts deterministic, discretized, generative, energy-based, diffusion, voxelized, and view-based policy formulations. It positions the proposed method as combining 3D scene representations with diffusion-based keypose prediction.
Key items:
- motivation: Diffusion policies are described as modeling action distributions with better mode coverage and fidelity than several alternatives.
- baseline: Prior manipulation policies discussed include RT-1, RT-2, GATO, BC-Z, InstructRL, Transporter Networks, C2F-ARM, PerAct, Act3D, and RVT.
- claim: The paper states that diffusion models had not yet been combined with 3D scene representations for this policy setting.
- other: ChainedDiffuser is described as complementary because it links keyposes with trajectories, while this paper predicts the next 3D keypose.

[s3] 3D Diffuser Actor Formulation
Summary: This section formulates 3D keypose prediction as conditional diffusion over end-effector translations and rotations. It reviews denoising diffusion probabilistic models and defines the conditional denoising objective for robot action prediction. It also describes inference as iterative denoising from Gaussian noise.
Key items:
- method_component: The action variable consists of 3D position and 6D rotation representation for the next end-effector keypose.
- method_component: The conditioning context includes calibrated RGB-D images, language instruction, and a short end-effector history.
- method_component (Equation 1): The denoising network predicts the noise or error for a noisy action sample at diffusion step t.
- method_component (Equation 2): Sampling starts from Gaussian noise and applies the learned denoiser repeatedly according to a sampling schedule.

[s4] Architecture, Training, and Implementation
Summary: This section details the model architecture, including the scene-language encoder, 3D grounding of noisy action estimates, 3D relative position diffusion transformer, denoising updates, training losses, and implementation details. The method uses frozen CLIP encoders, RGB-D lifting to a 3D feature cloud, rotary relative position embeddings, and separate position and rotation denoising schedules.
Key items:
- method_component: Multi-view RGB-D images are encoded by a frozen CLIP ResNet50 image encoder, lifted to a 3D feature cloud using depth and camera intrinsics, and paired with frozen CLIP language tokens.
- method_component (Figure 2): The noisy action estimate is represented both by an MLP feature and as a 3D entity at its workspace location.
- method_component (Equation 3): 3D rotary relative position embeddings make attention depend on relative positions and are described as translation-invariant.
- method_component (Equations 4, 5, and 6): The model predicts position residual, rotation residual, and gripper open/close state.
- method_component: The paper uses a scaled-linear scheduler for position denoising and a squared-cosine scheduler for rotation denoising.
- other: Implementation uses 256 by 256 images, farthest point sampling of 20% of 3D points, FiLM conditioning, BiRRT motion planning, and L1 plus BCE losses.

[s5] Experiments: Setup, Datasets, Baselines, and Metrics
Summary: This section defines the evaluation questions and experimental setup for simulation and real-world manipulation. The simulation evaluation uses RLBench with multi-task, multi-variation training and testing. The paper compares against prior 2D and 3D policy methods and ablated model variants.
Key items:
- dataset (Section 4.1): RLBench multi-task setting with 18 tasks and 249 variations using a Franka Panda robot in CoppeliaSim.
- dataset (Section 4.1): Training uses 100 demonstrations per RLBench task and testing uses 100 unseen episodes per task.
- baseline: Baselines include InstructRL, PerAct, Act3D, RVT, 2D Diffuser Actor, and 3D Diffuser Actor -RelAtt.
- metric: Task completion success rate is the main evaluation metric.
- ablation: 2D Diffuser Actor removes 3D scene encoding and uses pooled per-image 2D representations.
- ablation: 3D Diffuser Actor -RelAtt uses non-relative attention and does not ground the gripper estimate in the scene.

[s6] Simulation Results and Ablations
Summary: This section reports multi-task RLBench results, single-task RLBench results, ablations, and inference latency. 3D Diffuser Actor is reported to outperform prior baselines on many tasks and to outperform ablated variants using 2D features or non-relative attention. The section also reports slower per-keypose inference than Act3D.
Key items:
- result (Table 1): On 18 RLBench tasks, 3D Diffuser Actor reaches 77% average success and average rank 1.4.
- result (Table 1): The paper reports 77% average success versus 65% for the previous best listed baseline on the RLBench multi-task table.
- result (Table 1): Reported large task gains include stack blocks, screw bulb, put in cupboard, insert peg, and place cups.
- result (Figure 4): On 34 single-task RLBench tasks, the paper reports an average absolute margin of 6% over InstructRL and Act3D across tested categories.
- ablation (Table 2): On 5 HiveFormer tasks, 3D Diffuser Actor achieves 68.5 average success, 2D Diffuser Actor 40, and -RelAtt 62.
- result (Table 3): Reported inference time per keypose is 3 seconds for 3D Diffuser Actor and 0.12 seconds for Act3D.

[s7] Real-World Evaluation
Summary: This section evaluates 3D Diffuser Actor on five real-world manipulation tasks with a Franka Emika robot and one Azure Kinect RGB-D sensor. It describes the data collection setup, number of demonstrations, and task success rates. The paper reports examples of multimodal predictions in similar scene configurations.
Key items:
- dataset (Section 4.3): Real-world tasks are pick a bowl, stack bowls, put grapes in bowls, fold a towel, and press sanitizer.
- dataset (Section 4.3): Each real-world task uses 20 keypose demonstrations.
- metric: The real-world metric is average success rate for each task.
- result (Table 4): Reported real-world success rates are 100 for pick bowl, 100 for stack bowl, 50 for put grapes, 70 for fold towel, and 100 for press sanitizer.
- result (Figure 5): The paper visualizes different predicted manipulation modes, including picking a bowl with different poses and putting different grapes into a bowl.

[s8] Limitations, Conclusion, and Appendix
Summary: The limitations section lists inference latency, requirements for depth and calibration, kinesthetic demonstration supervision, lack of non-visual modalities, and quasi-static benchmark tasks. The conclusion restates the method and reported results, and the appendix provides a detailed architecture diagram and a visualization of the rotation noise scheduler. Future work includes larger-scale training in domain-randomized simulation and extensions to dynamic tasks or additional sensing modalities.
Key items:
- stated_limitation (Section 4.4): Multiple denoising iterations cause higher inference latency than non-diffusion baselines.
- stated_limitation (Section 4.4): The method requires camera calibration and depth information for 3D scene representations.
- stated_limitation (Section 4.4): The method requires kinesthetic demonstrations, which the paper states are hard to collect.
- stated_limitation (Section 4.4): The method considers only visual sensory input, not audio, tactile input, or force feedback.
- stated_limitation (Section 4.4): RLBench tasks are quasi-static, and dynamic tasks are left as future work.
- other (Appendix A): The appendix gives a detailed model diagram and compares rotation denoising behavior under scaled-linear and square-cosine schedulers.

GLOBAL INDEX
Claims:
- [s1] 3D Diffuser Actor combines diffusion policies and 3D scene representations for language-conditioned robot manipulation.
- [s1] The paper claims a 12 percentage-point absolute improvement over the prior state of the art on RLBench.
- [s2] The paper states prior diffusion policies had not yet been combined with 3D scene representations for this setting.
- [s4] The paper describes 3D grounding and relative 3D attention as making predictions translation-invariant.
- [s6] The paper reports that both 3D scene encodings and 3D relative attentions improve performance in ablations.
Method components:
- [s3] Conditional diffusion over 3D end-effector keyposes.
- [s3] Action representation with 3D position, 6D rotation, and binary gripper open/close state.
- [s4] Frozen CLIP ResNet50 image encoder and frozen CLIP language encoder.
- [s4] RGB-D lifting from 2D feature maps into a 3D feature cloud using depth and camera intrinsics.
- [s4] 3D grounding of the current noisy end-effector estimate as a scene entity.
- [s4] 3D relative position diffusion transformer using rotary positional embeddings.
- [s4] Separate denoising updates for position and rotation residuals.
- [s4] Scaled-linear scheduler for positions and squared-cosine scheduler for rotations.
- ... 1 more
Datasets:
- [s5] RLBench multi-task multi-variation benchmark with 18 tasks and 249 variations.
- [s5] RLBench setup uses four RGB-D cameras: front, wrist, left shoulder, and right shoulder.
- [s5] 100 demonstrations per RLBench task for training and 100 unseen episodes per task for testing.
- [s6] Additional single-task RLBench evaluation on 34 tasks across multimodal, long-term, visual occlusion, and tools categories.
- [s7] Real-world Franka Emika setup with Azure Kinect RGB-D sensor and five manipulation tasks.
- [s7] 20 keypose demonstrations per real-world task.
Baselines:
- [s5] InstructRL.
- [s5] PerAct.
- [s5] Act3D.
- [s5] RVT.
- [s5] 2D Diffuser Actor.
- [s5] 3D Diffuser Actor -RelAtt.
Ablations:
- [s5] 2D Diffuser Actor replaces 3D scene encoding with pooled multi-view 2D image features.
- [s5] 3D Diffuser Actor -RelAtt removes 3D grounding and relative attention, using standard attention instead.
- [s6] Ablations are evaluated on reach_and_drag, hang_frame, slide_cabinet, stack_cups, and open fridge.
- [s8] Appendix compares scaled-linear and square-cosine noise schedulers for 6D rotation denoising.
Metrics:
- [s5] Task completion success rate.
- [s6] Average success and average rank for RLBench multi-task evaluation.
- [s6] Inference time per keypose.
- [s7] Per-task real-world average success rate.
Results:
- [s6] 3D Diffuser Actor reports 77% average success and average rank 1.4 on 18 RLBench tasks.
- [s6] On RLBench multi-task evaluation, the paper reports 77% average success for 3D Diffuser Actor versus 65% for the previous best listed baseline.
- [s6] Reported single-task RLBench performance exceeds InstructRL and Act3D by an average absolute margin of 6% across tested categories.
- [s6] Ablation results report 68.5 average success for 3D Diffuser Actor, 40 for 2D Diffuser Actor, and 62 for -RelAtt.
- [s6] Inference time per keypose is reported as 3 seconds for 3D Diffuser Actor and 0.12 seconds for Act3D.
- [s7] Real-world success rates are reported as 100, 100, 50, 70, and 100 for the five tested tasks.
Stated limitations:
- [s8] Multiple denoising iterations increase inference latency.
- [s8] The method requires camera calibration and depth information.
- [s8] The method requires kinesthetic demonstrations.
- [s8] The method uses only visual sensory input.
- [s8] RLBench tasks are quasi-static, and dynamic tasks are future work.
```

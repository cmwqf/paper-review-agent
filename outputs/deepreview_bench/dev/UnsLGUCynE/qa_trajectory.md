# Q&A Trajectory

## Contribution

### Q1

**Question:** Using external scholarly retrieval if possible, how novel is the paper’s core claim of combining diffusion-based action/keypose prediction with 3D scene representations for language-conditioned robot manipulation? Please compare specifically to prior works such as Diffusion Policy, ChainedDiffuser, PerAct, Act3D, RVT, and any contemporaneous 3D/diffusion manipulation policies.

**Answer:** The core claim appears meaningfully novel as a combination: diffusion-based prediction of the next 3D end-effector keypose conditioned on language and explicit 3D scene representations. Relative to Diffusion Policy, the novelty is adding explicit calibrated RGB-D/3D scene grounding and language-conditioned keypose prediction, rather than primarily action diffusion over visual or low-dimensional observations. Relative to PerAct, Act3D, and RVT, the novelty is replacing deterministic/discretized 3D keypose prediction with a diffusion model intended to better capture multimodal demonstrations. Relative to ChainedDiffuser, the distinction is narrower but still real: ChainedDiffuser uses diffusion for trajectories conditioned on a 3D scene feature cloud and a target keypose, whereas this paper diffuses the next 3D keypose itself. Thus, the contribution is not a wholly new paradigm, since both diffusion robot policies and 3D manipulation policies already existed, and ChainedDiffuser was already close in using 3D scene-conditioned diffusion. However, based on the provided paper text and failed external retrieval, the specific integration for language-conditioned multi-task 3D keypose prediction seems plausibly novel and contribution-relevant.

**Impact:** strength, C2, confidence=medium

**Evidence:**
- paper: The paper states that diffusion models had been used for state-conditioned action distributions from low-dimensional and visual sensory input, but “They have not been yet combined with 3D scene representations.”
- paper: The paper distinguishes ChainedDiffuser as using a trajectory diffusion model conditioned on a 3D scene feature cloud and target 3D keypose to link keyposes, while “3D Diffuser Actor instead predicts the next 3D keypose for the robot's end-effector using 3D scene-conditioned diffusion.”
- paper: The paper map reports comparisons to PerAct, Act3D, and RVT as prior 3D policy methods, and reports ablations showing 3D Diffuser Actor outperforming a 2D Diffuser Actor and a variant without relative 3D grounding/attention.
- retrieval: External scholarly search attempts for combinations of “3D Diffuser Actor,” “diffusion policy,” “3D scene representation,” “language conditioned robot manipulation,” “ChainedDiffuser,” “PerAct,” “Act3D,” and “RVT” returned no retrieved papers beyond the provided paper text and references.
- inference: The novelty is best characterized as a strong synthesis rather than a fully independent conceptual leap: diffusion policies, 3D scene representations, and language-conditioned manipulation were each established, but the specific diffusion-over-3D-keyposes formulation with explicit 3D grounding appears distinct from the named baselines.

### Q2

**Question:** Using external scholarly retrieval if possible, are there contemporaneous or prior works not emphasized in the paper that combine diffusion policies with point clouds/RGB-D/3D representations for robot manipulation (e.g., DP3, 3D diffusion policy variants, point-cloud diffusion policies), and would they materially weaken the novelty of 3D Diffuser Actor’s contribution?

**Answer:** Yes, there are contemporaneous or near-prior works that partly overlap with the broad idea of combining diffusion-style action/pose generation with 3D robot representations, but the retrieved evidence does not fully erase the paper’s more specific contribution. The most relevant prior/contemporaneous item from retrieval is “Language-Conditioned Affordance-Pose Detection in 3D Point Clouds” from 2023, which uses a language-guided diffusion model to generate 6-DoF poses from 3D point clouds for robotic affordance-pose detection. The paper itself also discusses ChainedDiffuser, which conditions a trajectory diffusion model on a 3D scene feature cloud and a target 3D keypose. These works weaken the paper’s broad claim that diffusion models had “not yet been combined with 3D scene representations,” because at least related 3D point-cloud/scene-conditioned diffusion manipulation methods existed or were contemporaneous. However, they do not appear to match 3D Diffuser Actor’s exact setting: language-conditioned multi-task end-effector keypose policy learning on RLBench using RGB-D-lifted 3D scene features, grounding the noisy action estimate in the workspace, and iterative 3D translation/rotation denoising for the next keypose. The retrieved “Generalizable Humanoid Manipulation with Improved 3D Diffusion Policies” is 2024 and is therefore more likely contemporaneous/follow-on than prior to the September 2023 submission. Searches for DP3/“3D Diffusion Policy” did not retrieve the canonical DP3 paper in the provided retrieval results, so I would not count DP3 as established prior evidence here. Overall, this is a Contribution weakness: the novelty should be framed more narrowly and the related-work claim softened, but the paper still appears to retain a meaningful contribution in its specific architecture and benchmark setting.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper claims in the abstract that it “marries diffusion policies and 3D scene representations for robot manipulation” and reports gains over 3D policies and 2D diffusion policies on RLBench.
- paper: In related work, the paper states that prior diffusion models for imitation learning “have not been yet combined with 3D scene representations,” while also acknowledging ChainedDiffuser as a trajectory diffusion model conditioned on a 3D scene feature cloud and target 3D keypose.
- retrieval: External retrieval found “Language-Conditioned Affordance-Pose Detection in 3D Point Clouds” from 2023, whose abstract says it generates 6-DoF poses with a language-guided diffusion model based on 3D point clouds for robotic applications.
- retrieval: External retrieval found “Generalizable Humanoid Manipulation with Improved 3D Diffusion Policies” from 2024, suggesting contemporaneous or follow-on work in 3D diffusion policies, but not clear prior art to the 2023-09-21 submission.
- retrieval: Searches specifically targeting DP3 / “3D Diffusion Policy” did not retrieve the canonical DP3 paper in the provided results, so it should not be treated as confirmed prior evidence from this retrieval record.
- inference: The overlap is material for the breadth of the novelty claim, because 3D point-cloud-conditioned diffusion for robot pose/action-like outputs was not unique in the broader literature. It is less damaging to the narrower contribution, because the retrieved papers do not clearly provide the same multi-task RGB-D/language-conditioned next-keypose policy with 3D grounded denoising and RLBench evaluation.

**Retrieved Papers:**
- Language-Conditioned Affordance-Pose Detection in 3D Point Clouds | 2023 | https://www.semanticscholar.org/paper/099220023d6950a0d60fd7fd33c16257b3edf4ee | High: uses 3D point clouds and a language-guided diffusion model to generate 6-DoF poses for robotic affordance/pose tasks; overlaps with the broad novelty claim but not the full policy-learning setting.
- Generalizable Humanoid Manipulation with Improved 3D Diffusion Policies | 2024 | https://www.semanticscholar.org/paper/2211041f4b09aa0d60e2e917b88d14f3daaaa963 | Medium: directly suggests 3D diffusion policies for manipulation, but year 2024 makes it contemporaneous or follow-on rather than clear prior art to the ICLR 2024 submission.
- RoboCook: Long-Horizon Elasto-Plastic Object Manipulation with Diverse Tools | 2023 | https://www.semanticscholar.org/paper/c53a121d6c99f8c2add0eddca41262c7fc0bd795 | Low: uses point-cloud scene representations for manipulation but the retrieved abstract does not indicate a diffusion policy.
- Learning Hybrid Actor-Critic Maps for 6D Non-Prehensile Manipulation | 2023 | https://www.semanticscholar.org/paper/1d21fed83a9d7908b48aff0a08ae47f0c9abcc80 | Low: relevant to point-cloud manipulation and 6D action representations, but uses actor-critic reinforcement learning rather than diffusion.
- Multi-Stage Reinforcement Learning for Non-Prehensile Manipulation | 2023 | https://www.semanticscholar.org/paper/dcbe972843e6ea07d9325305a2d409aa4a155709 | Low: uses point-cloud representations for manipulation, but not retrieved as a diffusion-policy method.
- DexArt: Benchmarking Generalizable Dexterous Manipulation with Articulated Objects | 2023 | https://www.semanticscholar.org/paper/9bdcf270bce9f680bad5385bc7920536d4fa0c53 | Low: relevant to 3D representation learning for manipulation, but not evidence of diffusion-policy-plus-3D novelty overlap.

### Q3

**Question:** Using external scholarly retrieval if possible, how significant and broadly impactful are the paper’s empirical contributions on RLBench and real-world tasks? Please assess whether the reported 12-point RLBench gain over PerAct/Act3D/RVT-style baselines and small real-world evaluation represent a meaningful advance for the field, or whether the impact is narrowed by benchmark/task limitations, latency, data assumptions, or contemporaneous stronger methods.

**Answer:** The empirical contribution appears meaningful but not field-transforming. The reported 77% average success on 18 multi-task RLBench tasks, compared with 65% for the strongest listed prior baseline, is a substantial 12-point absolute gain on a recognized manipulation benchmark and supports the paper’s contribution claim. The ablations also suggest that the gain is not merely from using diffusion, but from combining diffusion with 3D scene grounding and relative 3D attention. This is a real contribution for language-conditioned 3D manipulation policies.

However, the breadth of impact is narrowed. The RLBench evaluation is still limited to 18 quasi-static simulated tasks in the main multi-task setting, and the paper itself notes that dynamic tasks are left for future work. The real-world evaluation is promising but small: five tasks, 20 demonstrations per task, and mixed success, including 50% on put-grapes-in-bowls and 70% on towel folding. The method also has practical constraints: 3 seconds per keypose versus 0.12 seconds for Act3D, plus requirements for calibrated RGB-D sensing and kinesthetic demonstrations. External scholarly retrieval did not return additional papers, so I cannot verify whether contemporaneous stronger methods reduce the novelty of the reported RLBench result. Based on the provided paper evidence alone, the empirical results are an important contribution, but the impact should be framed as a strong benchmark advance with limited demonstrated real-world scale and deployment practicality, rather than a broadly validated robotics breakthrough.

**Impact:** strength, C2, confidence=medium

**Evidence:**
- paper: The paper reports 77% average success and average rank 1.4 on 18 RLBench multi-task tasks, versus 65% for the previous best listed baseline, giving the claimed 12 percentage-point gain.
- paper: Ablations report 68.5 average success for the full 3D Diffuser Actor, 40 for the 2D Diffuser Actor, and 62 for the variant without relative attention, supporting the contribution of 3D scene encoding and relative 3D grounding.
- paper: The real-world evaluation covers five tasks with 20 keypose demonstrations per task and reports success rates of 100, 100, 50, 70, and 100, which is encouraging but small and uneven.
- paper: The paper reports inference latency of 3 seconds per keypose for 3D Diffuser Actor compared with 0.12 seconds for Act3D, and lists limitations including depth and calibration requirements, kinesthetic demonstrations, visual-only sensing, and quasi-static RLBench tasks.
- retrieval: The provided scholarly retrieval attempts returned no retrieved papers, so there is no external evidence here confirming or refuting the reported state-of-the-art comparison or identifying contemporaneous stronger methods.
- inference: For the Contribution dimension, a double-digit gain over strong 3D manipulation baselines on RLBench is significant, but the limited real-world scale, high latency, and dependence on calibrated RGB-D and demonstration assumptions reduce the breadth of empirical impact.

## Soundness

### Q1

**Question:** Do the simulation and real-world experiments report multiple random seeds, confidence intervals, standard errors, or statistical significance tests for success rates, especially for the claimed 12-point RLBench improvement and the real-world results?

**Answer:** No. The paper reports point estimates of success rates, but I found no reporting of multiple random seeds, confidence intervals, standard errors, or statistical significance tests for the simulation or real-world success rates. For RLBench, the paper states that models are tested on 100 unseen episodes per task and reports a 77% average success rate, claiming a 12 percentage-point absolute improvement over Act3D. For the real-world tasks, it reports per-task success rates such as 100, 100, 50, 70, and 100, but does not state the number of evaluation trials, variability across runs, or uncertainty intervals. This weakens the soundness of the empirical claims because the main improvement and real-world results are presented without quantified uncertainty or evidence that they are robust to training/evaluation randomness.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: The paper defines the metric as task-completion success rate: “the proportion of execution trajectories that lead to goal conditions specified in language instructions” and states that RLBench testing uses “100 unseen episodes for each task” (lines 184, 207).
- paper: The main RLBench claim is reported as a point estimate: “It achieves an average 77% success rate, an absolute improvement of 12% over Act3D, the previous state-of-the-art” (line 209).
- paper: The real-world setup reports 20 keypose demonstrations per task and says “The evaluation metric is average success rate of each task,” followed by Table 4 with only point success values: pick bowl 100, stack bowl 100, put grapes 50, fold towel 70, press sanitizer 100 (lines 214-222, 242).
- inference: A targeted search for “seed confidence interval standard error significance random” returned no matches, and the inspected experiment/result sections show only point estimates without uncertainty measures or significance tests.

### Q2

**Question:** Are the main RLBench baselines (InstructRL, PerAct, Act3D, RVT, and 2D Diffuser Actor) evaluated under the same training data, task split, observation modalities, and test protocol as 3D Diffuser Actor, or are any results copied from prior papers with potentially different settings?

**Answer:** No: the paper does not establish that all main RLBench baselines were rerun under exactly the same conditions as 3D Diffuser Actor. It explicitly states that InstructRL, PerAct, Act3D, and RVT results are reported from the corresponding prior papers, while 2D Diffuser Actor is the authors' own implementation/ablation. Although the paper describes a common RLBench setup for “our model and baselines” with 18 tasks, 249 variations, 100 demonstrations per task, four RGB-D cameras, 100 test episodes, and a max of 50 executed actions, this is only clearly controlled for the authors' own models; the copied prior-paper results may differ in implementation details, observation processing, training protocol, or evaluation protocol. This weakens the soundness of the SOTA comparison and the claimed +12 percentage-point gain, because the main baseline numbers are not clearly produced under a fully matched experimental protocol.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: The baseline paragraph says: “For InstructRL, PerAct, Act3D and RVT we report the results from the corresponding papers.” This directly indicates those baselines were not necessarily rerun by the authors under the same pipeline.
- paper: The same paragraph distinguishes “2D Diffuser Actor” as “our implementation,” created by removing the 3D scene encoding from 3D Diffuser Actor and using pooled per-view 2D representations, so this baseline appears to be evaluated in the authors' controlled setup.
- paper: The dataset/evaluation paragraph states that the authors use four RGB-D cameras, 100 demonstrations per task, 100 unseen test episodes per task, and at most 50 actions during evaluation, but this statement is not reconciled with the later admission that several baseline results are copied from prior papers.
- inference: Because the strongest comparisons to PerAct, Act3D, RVT, and InstructRL rely on prior-paper numbers, exact equality of training data, task splits, observation modalities, and test protocol is not demonstrated from the paper text. This is especially important because the paper’s headline RLBench improvement is computed against Act3D/RVT/PerAct numbers in Table 1.

### Q3

**Question:** Do the ablation studies adequately isolate the claimed technical contributions—3D scene encoding, 3D grounding/relative attention, and the diffusion formulation/schedulers—or are important components missing or confounded?

**Answer:** The ablations only partially isolate the claimed contributions. They provide some evidence for the benefit of 3D scene representations and for the combined 3D grounding/relative-attention design, but they are too limited to fully support all technical claims. The paper reports only two ablated variants: a “2D Diffuser Actor” replacing the 3D scene encoding with pooled 2D image features, and “3D Diffuser Actor -RelAtt,” which uses absolute/non-relative attention and removes the 3D grounding of the gripper estimate. This means the grounding mechanism and relative positional attention are confounded rather than independently isolated. The ablation table is also small: it reports only average success over 5 HiveFormer RLBench tasks, not the full 18-task or 34-task evaluation suite and not per-task results. Most importantly, the diffusion formulation itself is not ablated against a non-diffusion 3D keypose model with the same scene encoder/architecture, nor are denoising iteration count, sampling schedule, or the separate position/rotation schedulers evaluated quantitatively. The scheduler choice is justified by a statement about faster convergence and an appendix visualization, but not by a controlled success-rate ablation. Therefore, the ablations support the broad claim that 3D representations help, but they do not cleanly establish the independent contributions of 3D grounding, relative 3D attention, or the diffusion/scheduler design.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: Section 4.2 states that the authors ablate “the use of 3D scene representations and relative attentions” and train multi-task policies on only 5 RLBench/HiveFormer tasks: reach_and_drag, hang_frame, slide_cabinet, stack_cups, and open fridge.
- paper: Table 2 reports only three average-success numbers: 3D Diffuser Actor 68.5, 2D Diffuser Actor 40, and 3D Diffuser Actor -RelAtt 62. The caption concludes that “Both 3D scene encodings and 3D relative attentions matter in performance.”
- paper: The text explains the 2D-vs-3D comparison as follows: “3D Diffuser Actor largely outperforms its 2D counterpart where the input images are featurized, pooled and fed into the model.”
- paper: The same section says “Our model with absolute attentions performs worse than our model with relative attentions,” but the paper map and ablation description indicate that the -RelAtt variant also removes grounding of the gripper estimate in the scene, so the causal effect of relative attention alone is not isolated.
- paper: The method section defines two noise schedulers and states that using scaled-linear position denoising and squared-cosine orientation denoising “converge much faster than using squared cosine noise for both,” with appendix justification for square-cosine rotation scheduling. However, the reported ablation table does not include scheduler variants or task-success comparisons for diffusion design choices.
- inference: Because the full model is compared only to a 2D pooled-feature diffusion variant and a combined no-relative/no-grounding variant, the ablation design cannot distinguish whether gains come from 3D lifting, point-cloud capacity, grounding the noisy action estimate, relative positional attention, diffusion sampling, or scheduler choices. This is a methodological weakness for soundness because several central technical contributions remain untested or confounded.

### Q4

**Question:** Does the paper provide enough technical detail and justification for the diffusion action parameterization and inference procedure—especially rotation denoising with 6D rotations, separate position/rotation schedulers, number of denoising steps, and conversion to executable robot actions—to assess whether the method is well-defined and reproducible?

**Answer:** No, not fully. The paper gives substantial technical detail for the high-level diffusion formulation: it defines the action as 3D position, 6D rotation, and binary gripper state; gives denoising equations for translation and rotation; specifies separate position and rotation noise schedulers; states that 6D rotations are used to avoid quaternion discontinuities; and says predicted keyposes are executed using BiRRT motion planning in RLBench and MoveIt! on the real robot. However, some details needed to make the inference procedure fully well-defined and reproducible appear under-specified from the provided text. In particular, the number of denoising steps T used at inference is not clearly stated, the exact handling of 6D rotation outputs as valid executable rotations is not described in enough detail, and the conversion from a denoised 6D rotation/keypose plus gripper prediction into a concrete robot command trajectory is only described at the level of using a motion planner. This matters for Soundness because the paper’s central method is an iterative diffusion action policy; if the rotation denoising and sampling/execution pipeline are underspecified, it is harder to verify that the reported method is mathematically well-defined, faithfully implementable, and reproducible.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: The paper states that an action consists of 3D position, 6D rotation, and binary gripper open/close state, and that rotations use the 6D representation of Zhou et al. to avoid quaternion discontinuities.
- paper: The paper provides denoising equations for position and rotation residuals and defines two noise schedulers: a scaled-linear scheduler with βmax and βmin set to 0.02 and 0.0001, and a squared-cosine scheduler. It says scaled-linear is used for position and squared-cosine for orientation, with additional appendix justification for rotation scheduling.
- paper: For execution, the paper states that at inference time the model denoises the next 3D keypose and that the predicted keypose is reached with a sampling-based motion planner; implementation details mention BiRRT in RLBench and the MoveIt! BiRRT planner for real-world experiments.
- retrieval: No retrieved papers were provided, so the judgment is based only on the supplied paper map and in-paper observations.
- inference: The provided text does not clearly identify the inference-time number of denoising steps T, nor does it fully specify how noisy or denoised 6D rotation vectors are projected/converted into valid executable end-effector orientations. The motion-planning step is described only at a high level, which limits reproducibility of the complete action pipeline.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall / ICLR format:** The paper generally follows an ICLR-style single-column layout with anonymized header and page numbers, and is visually inspectable. However, noticeable **colored revision-like text** and a **red strikethrough sentence** make it look unfinished/draft-like.

- **Page 1:** Clean title/abstract layout. Title wraps awkwardly with hyphenation in “Ma-nipulation,” which looks slightly unpolished but is readable.

- **Page 2, Figure 1:** Main visual is mostly legible and connected to the method description. Some internal labels in the architecture panels are small. Caption is informative, but very long and partially blue, which is visually distracting.

- **Page 3:** Large blocks of **orange and blue text** interrupt the normal typography and appear like tracked-change or author-note coloring. This is a significant presentation issue for an ICLR submission unless intentional hyperlink styling, which it does not resemble.

- **Page 4, Figure 2:** Architecture figure is informative and well connected to the caption, but many internal labels/arrows are small and require zooming. The red strikethrough sentence below the figure is a major formatting/draft artifact.

- **Pages 5–6, equations:** Equations are generally centered, numbered, and readable. Some inline variables/phrases appear blue, which may be hyperlink coloring or revision coloring; visually inconsistent. Equation spacing is mostly acceptable.

- **Page 7, Figure 3:** Task image grid is visually clear; task labels under images are small but readable. Caption is concise and connected to the figure. Layout has a slightly large gap after the figure but no serious issue.

- **Page 8, Table 1:** Dense but mostly legible. The table is compact with many columns; small task labels and numerical deltas may be hard to read in print or at normal zoom.

- **Page 8, Tables 2–3 and Figure 4:** Table 2 and Table 3 are readable, though Table 3 is very minimal. Figure 4’s plot/legend/axis labels are quite small and would benefit from enlargement. The page is float-heavy but still navigable.

- **Captions:** Generally informative and well connected to their visuals. Figure 1 and Figure 2 captions are detailed; Figure 3 and Figure 4 captions are concise. Some captions contain colored text, reducing professional polish.

- **Main presentation concerns:** Colored paragraphs, blue/orange/red text, and strikethrough formatting are the biggest issues. Several figures/tables contain small internal labels. Otherwise, margins, page numbering, section headings, and equation formatting are mostly clean.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

### Q2

**Question:** Please inspect the remaining PDF pages, especially the real-world results, limitations/conclusion, and appendix pages, for presentation quality: Are the real-world figures/tables and appendix diagrams legible, are captions explanatory, and do any formatting artifacts or notation/organization issues persist?

**Answer:** The remaining pages show several presentation weaknesses. The real-world results page is inspectable, but Table 4 is visually cramped in the PDF text extraction: task names and success values run together, e.g. “pick bowl 100stack bowl 100put grapes 50fold towel 70press sanitizer100,” which suggests poor table spacing/legibility. Figure 5 has only a very terse caption, “Visualized results of our real-world manipulation,” and the nearby labels appear awkwardly formatted with quotation marks and broken phrasing such as “press hand the sanitizer,” “fold the towel,” and “stack to the purple bowl.” This caption does not adequately explain what each panel shows or how the visualized modes support the paper’s real-world claim. The limitations and conclusion are organized in the expected sections, but formatting/proofreading artifacts persist, including missing spaces (“robust.5.”, “render3D”), typos (“exiting” for “exciting,” “test out model”), and inconsistent capitalization (“RLbench”). The appendix is reasonably organized into A.1 and A.2, and Figure 7 has a much more explanatory caption than Figure 5. However, Figure 6’s caption is minimal (“3D Diffuser Actor architecture in more detail”), and the extracted page gives no detailed legend in the caption itself, so readers must rely heavily on surrounding prose and the diagram’s internal labels. Overall, the appendix diagrams appear more usable than the real-world figure/table, but the paper still has noticeable captioning, spacing, and proofreading issues that reduce presentation quality.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: PDF page 9 shows Table 4 as “Task Success pick bowl 100stack bowl 100put grapes 50fold towel 70press sanitizer100,” indicating cramped formatting around the real-world success table.
- paper: PDF page 9 captions Figure 5 only as “Visualized results of our real-world manipulation,” with adjacent labels rendered as quoted fragments such as “press hand the sanitizer,” “fold the towel,” and “stack to the purple bowl.”
- paper: PDF page 9 limitations/conclusion contain formatting and proofreading artifacts: “robust.5.” lacks spacing before item 5, “render3D Diffuser Actor” lacks a space, and the prose includes “exiting future direction” and “test out model.”
- paper: PDF page 15 organizes the appendix into “A.1 Detailed Model Diagram” and “A.2 The Importance of Noise Scheduler,” but Figure 6’s caption is only “3D Diffuser Actor architecture in more detail.”
- paper: PDF page 16 gives Figure 7 a detailed caption explaining panels (a) clean rotation, (b) scaled-linear scheduler, (c) square-cosine scheduler, and (d) denoising performance curve, making this appendix figure comparatively more self-explanatory.
- inference: Because real-world evidence is important for assessing the paper’s empirical claims, weak formatting and under-explained captions on the real-world results page make the results harder to inspect and verify, even though the appendix organization is mostly clear.

# Paper Map

```text
PAPER MAP
Title: Chunking: Forgetting Matters in Continual Learning even without Changing Tasks
Authors: Anonymous authors
Venue: ICLR 2024
Submission date: 2023-09-18

SECTIONS
[s1] Abstract and Introduction
Summary: The paper decomposes continual learning into task/data-distribution shift and a chunking sub-problem where data is only available in sequential chunks. It argues that chunking accounts for a large part of the performance gap between offline learning and continual learning, and that forgetting occurs even without task shift. The section states contributions: defining and analyzing chunking, showing current CL methods do not improve over SGD in this setting, and proposing per-chunk weight averaging.
Key items:
- problem: Chunking problem: learning from sequential data chunks without revisiting previous chunks, even when there is no distribution shift.
- claim: Chunking is responsible for a significant part of the performance drop between offline learning and continual learning.
- claim: Current continual learning methods perform comparably to plain SGD in the task-shift-free chunking setting.
- claim: Forgetting is a key reason for reduced performance in chunking, not only a consequence of task shift.
- method_component: Per-chunk weight averaging is proposed as a simple method motivated by linear-case analysis.

[s2] Preliminaries and Related Work
Summary: This section defines standard continual learning, online continual learning, and the relationship between tasks and chunks. It situates chunking relative to online learning and prior work on catastrophic forgetting, online neural network learning, and weight averaging.
Key items:
- motivation (Figure 1): Standard CL commonly presents data as a sequence of tasks, while online CL splits tasks into smaller chunks.
- problem (Figure 1): The chunking setting is described as a reduced CL setting where the task does not change.
- other: Chunking is related to online learning without task shift, but uses batched chunks to match neural network training.
- motivation: The paper links forgetting without task shift to older work on catastrophic forgetting and the stability-plasticity dilemma.
- method_component: The paper considers per-chunk weight averaging rather than offline-learning weight averaging methods.

[s3] The Chunking Setting
Summary: This section formally defines chunking as learning from a sequence of non-revisited chunks drawn from the same distribution. It describes a balanced chunk construction procedure used in experiments and explains that the only difference from full CL is the absence of task shift.
Key items:
- method_component: A learner observes chunks C1 through CN and trains on one chunk at a time without revisiting previous chunks.
- problem: All chunks are drawn from the same distribution, so the setting removes distribution shift.
- method_component: Experiments use balanced chunks with approximately equal numbers of instances per class.
- dataset: A fixed-sized portion of data from each class is reserved as a test set for evaluating accuracy.
- claim: Performance in the chunking setting is presented as an upper bound to CL performance under the same data and model conditions.

[s4] Analysis of the Chunking Setting
Summary: This section measures how much chunking contributes to the performance gap from offline learning to CL, and analyzes performance and forgetting under different chunk sizes. It reports that chunking explains roughly half of the offline-to-CL accuracy drop in selected experiments and that CL methods do not outperform SGD in the chunking setting.
Key items:
- dataset (Table 1): CIFAR-100 and Tiny ImageNet are used with ResNet18 and 10 task/chunk splits to compare offline, chunking, and standard CL settings.
- metric (Table 1): End-of-training test accuracy and percentage of the offline-to-CL drop attributed to chunking are reported.
- result (Table 1): Chunking accounts for 50.05% of the offline-to-CL accuracy drop on CIFAR-100 and 46.69% on Tiny ImageNet with DER++.
- baseline (Figures 2 and 3): Plain SGD is compared with CL methods including DER++, ER, ER-ACE, AGEM, EWC, and GSS.
- result (Figures 2 and 3): Accuracy decreases as chunk size decreases; on CIFAR-100, accuracy drops from around 73% with the full dataset as one chunk to around 45% with chunk size 1000.
- result (Figures 4 and 5): Training loss and per-chunk training accuracy analyses show chunks are fit well, while accuracy on old chunks drops afterward, indicating forgetting.

[s5] Analysis of the Linear Case
Summary: This section analyzes linear regression under chunking using closed-form solutions. It contrasts per-chunk least squares, which forgets earlier chunks, with Bayesian linear regression, which aggregates information across chunks, and uses this to motivate weight averaging.
Key items:
- claim: Naive least squares on each arriving chunk fully forgets previous chunks because the convex solution depends only on the current chunk.
- method_component: Bayesian linear regression produces the same predictor for a given dataset regardless of chunking.
- method_component (Equations 1-5): Bayesian posterior mean and covariance update equations are presented for sequential chunks.
- stated_limitation: Storing the Bayesian precision matrix is infeasible for very large systems because it takes O(dim(theta)^2) space.
- method_component (Equations 6-7): Weight averaging is introduced as a memory-limited backoff that averages least-squares solutions from chunks.
- claim: When chunks are large enough for accurate covariance estimates, weight averaging should approximate Bayesian linear regression and forget less.

[s6] Per-Chunk Weight Averaging
Summary: This section applies the linear-case motivation to neural networks by averaging the network parameters obtained at the end of each chunk. It evaluates mean and exponential moving average variants and analyzes how the method preserves information from previous chunks.
Key items:
- method_component: Per-chunk weight averaging stores an average of end-of-chunk neural network weights and uses the averaged weights only for evaluation.
- method_component: The averaged weights include all neural network parameters, including batch normalization statistics.
- method_component (Equations 8-9): The paper evaluates both mean weight averaging and exponential moving average weight averaging.
- dataset: Experiments use CIFAR-10, CIFAR-100, and Tiny ImageNet with the same chunking setup as previous experiments.
- result (Figure 6): For the smallest chunk sizes evaluated, mean weight averaging improves accuracy by +4.32%, +8.22%, and +11.73% on CIFAR-10, CIFAR-100, and Tiny ImageNet respectively.
- result (Figure 6): Per-chunk mean weight averaging preserves higher accuracy on previous chunks than final SGD weights, indicating less forgetting.

[s7] Application to Continual Learning
Summary: This section tests whether per-chunk mean weight averaging transfers to full continual learning with task shift. It evaluates standard and online CL, class-incremental and task-incremental scenarios, and four CL methods across three datasets.
Key items:
- baseline (Table 2): CL methods evaluated with and without weight averaging are DER++, ER, AGEM, and GSS.
- dataset: CIFAR-10 is split into 5 tasks of 2 classes; CIFAR-100 and Tiny ImageNet are split into 10 tasks.
- metric (Table 2): Accuracy is reported for class-incremental and task-incremental learning in online and standard CL.
- result (Table 2): In standard CL, weight averaging improves average performance by +6.39%, +11.11%, +12.02%, and +11.36% for DER++, ER, AGEM, and GSS respectively.
- result (Table 2): In online CL, weight averaging improves average performance by +5.05%, +4.52%, +8.82%, and +3.68% for DER++, ER, AGEM, and GSS respectively.
- result (Table 2): Weight averaging performs worse than final weights for DER++ on CIFAR-10 and for GSS on Tiny ImageNet in some class-incremental cases.

[s8] Conclusions, Reproducibility Statement, and Appendices
Summary: The conclusion restates that chunking is an important sub-problem of CL, current CL methods do not address it in the studied setting, and per-chunk weight averaging improves chunking and often CL performance. The reproducibility statement says experimental details are provided and code is included in supplementary material. Appendices add experimental details, class-imbalance analysis, epoch-count analysis, extra forgetting curves, and EMA weighting experiments.
Key items:
- claim: Future work on chunking is stated to have the possibility of improving CL as a whole.
- other (Appendix A): Experiments use a modified Mammoth CL library, ResNet18 backbones, random crops, horizontal flips, SGD, batch size 32, and grid-searched hyperparameters.
- baseline (Appendix A): The full chunking-setting method list is AGEM, DER++, ER, ER-ACE, EWC, GSS, and plain SGD.
- ablation (Appendix B): Random, non-class-balanced chunk sampling is compared against balanced chunking.
- ablation (Appendix C): Different numbers of epochs per chunk are evaluated for SGD.
- ablation (Appendix E): Different EMA weighting values are evaluated for weight averaging.

GLOBAL INDEX
Claims:
- [s1] Chunking is a distinct continual learning sub-problem involving sequential chunks without revisiting past chunks.
- [s1] Chunking accounts for a large part of the performance drop between offline learning and CL.
- [s4] Current CL methods perform roughly the same as plain SGD in the chunking setting.
- [s4] Forgetting, rather than underfitting, explains the performance drop in the studied chunking setting.
- [s5] Weight averaging can approximate Bayesian linear regression when chunks are large enough for accurate covariance estimates.
- [s8] Work on chunking may improve continual learning more broadly.
Method components:
- [s3] Balanced chunking setup with chunks drawn from the same distribution and no task shift.
- [s5] Bayesian linear regression sequential posterior updates for analyzing forgetting under chunking.
- [s5] Linear-case weight averaging as a memory-limited approximation to Bayesian aggregation.
- [s6] Per-chunk mean weight averaging of end-of-chunk neural network parameters.
- [s6] Per-chunk EMA weight averaging controlled by alpha.
- [s7] Applying per-chunk mean weight averaging to DER++, ER, AGEM, and GSS in CL.
Datasets:
- [s4] CIFAR-10 for chunking performance and weight averaging experiments.
- [s4] CIFAR-100 for offline, chunking, CL, forgetting, and weight averaging experiments.
- [s4] Tiny ImageNet for offline, chunking, CL, forgetting, and weight averaging experiments.
- [s7] CIFAR-10 split into 5 tasks of 2 classes for CL experiments.
- [s7] CIFAR-100 split into 10 tasks for CL experiments.
- [s7] Tiny ImageNet split into 10 tasks for CL experiments.
Baselines:
- [s4] Offline SGD training.
- [s4] Plain SGD training in the chunking setting.
- [s4] DER++.
- [s4] ER and ER-ACE.
- [s4] AGEM, EWC, and GSS.
- [s7] CL methods without weight averaging are compared to WA-DER++, WA-ER, WA-AGEM, and WA-GSS.
Ablations:
- [s4] Varying chunk size in the chunking setting.
- [s6] Mean weight averaging versus EMA weight averaging.
- [s7] Online versus standard CL settings.
- [s7] Class-incremental versus task-incremental evaluation.
- [s8] Balanced chunks versus randomly sampled non-balanced chunks.
- [s8] Different numbers of training epochs per chunk and different EMA alpha values.
Metrics:
- [s4] End-of-training test accuracy.
- [s4] Percentage of offline-to-CL accuracy drop attributed to chunking.
- [s4] Training loss during learning on chunks.
- [s4] Accuracy on the training data of selected past chunks after each chunk.
- [s7] Class-incremental and task-incremental accuracy averaged over 3 runs with standard error.
Results:
- [s4] Chunking explains 50.05% of the offline-to-CL performance drop on CIFAR-100 and 46.69% on Tiny ImageNet using DER++.
- [s4] Accuracy drops as chunk size decreases across CIFAR-10, CIFAR-100, and Tiny ImageNet.
- [s4] CL methods are reported to perform roughly the same as plain SGD in the chunking setting.
- [s4] Chunk training data can reach 100% accuracy after learning the chunk, but accuracy on that chunk decreases after later chunks.
- [s6] Mean weight averaging improves smallest-chunk accuracy by +4.32%, +8.22%, and +11.73% on CIFAR-10, CIFAR-100, and Tiny ImageNet respectively.
- [s7] Per-chunk mean weight averaging generally improves performance in both online and standard CL across the tested methods and datasets.
Stated limitations:
- [s5] Bayesian linear regression precision storage is infeasible for very large systems because it requires O(dim(theta)^2) space.
- [s7] Per-chunk mean weight averaging is reported to perform worse than final weights for DER++ on CIFAR-10 and for GSS on Tiny ImageNet in some class-incremental cases.
- [s8] Class imbalance could be a problem for other datasets, although it is not significant in the paper's reported setup.
```

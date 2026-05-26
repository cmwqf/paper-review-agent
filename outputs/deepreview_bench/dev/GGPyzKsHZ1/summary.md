# Paper Map

```text
PAPER MAP
Title: Lifelong Audio-video Masked Autoencoder with Forget-robust Localized Alignments
Authors: Anonymous authors
Venue: ICLR 2024
Submission date: 2023-09-16

SECTIONS
[s1] Abstract and Introduction
Summary: The paper introduces task-free continual audio-video representation learning, where audio-video data distributions shift over time. It identifies sparse audio-video correlations and forgetting of learned cross-modal relationships as key challenges, and proposes FLAVA to select localized and forget-robust multimodal patches.
Key items:
- problem: Audio-video models are assumed to train on static distributions, while real-world video streams can shift across categories and environments.
- problem (Figure 2): The paper highlights sparse spatiotemporal correlation between audio and video patches and forgetting of audio-video relationships.
- claim: FLAVA addresses continual audio-video representation learning without task identification.
- method_component: Localized Alignment uses a small trainable multimodal encoder to predict well-aligned audio and video tokens.
- method_component: Forget-robust multimodal patch selection compares current and past patch importance to reduce drift of previous audio-video representations.
- result: The introduction reports improvements of 1.52%p, 1.80%p, and 0.31%p on audio-to-video retrieval, video-to-audio retrieval, and audiovisual classification.

[s2] Related Work
Summary: This section situates the paper relative to self-supervised audiovisual understanding and multimodal continual learning. It contrasts FLAVA with masked audio-video representation learners and continual learning approaches that require labels or task boundaries.
Key items:
- baseline: TVLT and CAV are discussed as masked audiovisual representation learning methods.
- baseline: IncCLIP and AV-CIL are discussed as multimodal continual learning methods.
- claim: The paper states that prior audiovisual masked modeling methods assume a fixed input distribution.
- claim: The paper states that some multimodal continual learning approaches require dense labels or task boundary information.

[s3] Continual Audio-Video Representation Learning
Summary: This section formalizes the task-free continual audio-video pre-training setup over a sequence of disjoint unsupervised datasets. It defines audio/video patch embeddings and the base reconstruction plus masked contrastive objective, then analyzes forgetting of audio-video alignments using attention map visualizations.
Key items:
- problem (Section 3.1): The model trains on a sequence of disjoint unsupervised audio-video datasets without explicit knowledge of task boundaries.
- method_component (Equation 1): Audio spectrograms and video clips are patchified and embedded through convolutional layers.
- method_component (Section 3.1): The base pre-training loss combines masked reconstruction loss and masked contrastive loss.
- problem (Figure 3): Cross-attention with mismatched past and current audio-video data can focus on misleading regions.
- claim (Section 3.2): The paper argues that spurious cross-modal correlations can overwrite earlier audio-video alignments.

[s4] Lifelong Audio-Video Masked Autoencoder with FLAVA
Summary: This section presents the FLAVA method: an Audio-Video Matching module for localized alignment, a pruning-probability computation comparing current and past attention, and audio/video patch selection for continual masked modeling. It also introduces FLAVA+, which stores selected patches rather than raw data in memory.
Key items:
- method_component (Equation 2): The AVM module computes audio-to-video and video-to-audio cross-attention maps.
- method_component (Equation 3): Importance scores are produced by mean-pooling cross-attention maps for audio and video patches.
- method_component (Equations 4 and 5): Forget-robust patch selection compares attention induced by current queries and past memory queries.
- method_component (Algorithm 2): Audio patches are selected in time chunks to preserve temporal continuity in spectrogram patches.
- method_component (Equation 6): Video selection masks patches with high pruning probability and samples from remaining importance scores.
- method_component (Section 4.3): The final objective is reconstruction loss plus masked contrastive loss plus a DER++-style memory penalty loss.

[s5] Experiments: Setup
Summary: This section defines evaluation for task-free lifelong audio-video representation learning on VGGSound and AudioSet. It describes downstream zero-shot retrieval and audiovisual classification tasks, continual learning baselines, and metrics for accuracy and forgetting.
Key items:
- dataset (Section 5.1): Experiments use VGGSound and AudioSet, both containing 10-second YouTube videos.
- baseline (Section 5.1): Baselines include ER, MIR, DER++, GMED, CLS-ER, LUMP, Finetune, and Multitask.
- metric (Table 1): Zero-shot retrieval is evaluated with R@K and continual-learning average accuracy and average forgetting.
- metric (Table 4): Audiovisual classification uses accuracy on VGGSound and mAP on AudioSet, with average accuracy and average forgetting.
- metric (Table 2): Efficiency is measured using GPU memory and throughput.

[s6] Experiments: Quantitative Results and Analysis
Summary: This section reports retrieval, classification, efficiency, ablation, and modality-gap analyses. FLAVA and FLAVA+ are compared with continual learning baselines under the same task-free setting.
Key items:
- result (Table 1): On VGGSound retrieval, FLAVA and FLAVA+ improve average audio-to-video scores by 1.52%p and 2.80%p, and video-to-audio scores by 1.80%p and 3.26%p over baselines.
- result (Table 1): On AudioSet retrieval, FLAVA and FLAVA+ report average audio-to-video gains of 0.03%p and 2.94%p, and video-to-audio gains of 0.58%p and 3.76%p.
- result (Table 2): FLAVA uses 17.45 GB GPU memory, compared with 30.95 GB for DER++, and reports throughput of 17.43 samples/sec.
- result (Table 4): On audiovisual classification, FLAVA and FLAVA+ improve over baselines on VGGSound and AudioSet average scores.
- ablation (Table 3): Ablations compare Random, MATS, LAVA-only, FRS-only, and full FLAVA patch selection.
- result (Figure 5): Modality-gap analysis reports that FLAVA maintains the highest modality gap across tasks among compared methods.

[s7] Conclusion and Reproducibility Statement
Summary: The conclusion restates the task-free continual audio-video learning problem and the observed issues of sparse correlation and forgetting. The reproducibility statement says the code is based on RepLAI, TVLT, and CAV, with experimental details and supplementary code provided.
Key items:
- claim: The paper states that FLAVA adaptively captures sparse audio-video attention while mitigating forgetting without task identification.
- other (Section 7): The authors state that experimental setup details are in Section 5 and Appendix A.
- other (Section 7): The authors state that code is included in supplementary material and will be publicly released.

[s8] Appendix
Summary: The appendix provides implementation details, evaluation protocol, objective definitions, AVM training, additional experiments, hyperparameter tuning, additional modality-gap analysis, audio selection pseudocode, visualization examples, and limitations. It includes dataset split statistics and extra downstream evaluations such as AVE and sound source localization.
Key items:
- dataset (Figure 6): VGGSound is split into 8 tasks; AudioSet is split into 7 tasks based on class hierarchy.
- method_component (Appendix D): AVM is trained with positive and negative audio-video pairs using a binary audio-video matching objective.
- ablation (Appendices E and F): Additional experiments vary rehearsal memory size, audio patch selection strategy, task order, sampling ratios, and AVM temperature.
- result (Table 8): On AVE event localization, FLAVA and FLAVA+ report 56.68 accuracy, compared with 57.73 for Multitask.
- stated_limitation (Figure 12): In sound source localization, the paper states that all methods fail to accurately pinpoint exact sound-source locations, attributed mainly to backbone limitations.
- stated_limitation: The appendix organization states that Appendix K outlines limitations of the study.

GLOBAL INDEX
Claims:
- [s1] FLAVA continually learns audio-video representations under shifting data distributions without requiring task identification.
- [s1] Sparse spatiotemporal audio-video correlation and forgetting of audio-video relationships are presented as core challenges.
- [s2] Prior audiovisual masked-modeling methods are described as assuming fixed input distributions.
- [s3] Cross-modal attention with mismatched current and past data can induce misleading or spurious alignments.
- [s7] The paper claims FLAVA captures sparse audio-video attention and mitigates forgetting of previous relationships.
Method components:
- [s3] Task-free continual pre-training over disjoint unsupervised audio-video datasets.
- [s3] Patchification and convolutional embedding of audio spectrogram and video inputs.
- [s3] Masked reconstruction loss and masked contrastive loss for audio-video pre-training.
- [s4] Audio-Video Matching module for cross-modal attention and localized audio-video alignment.
- [s4] Importance-score computation from mean-pooled cross-attention maps.
- [s4] Forget-robust pruning probability using current and past queries from rehearsal memory.
- [s4] Audio time-chunk patch selection and video importance-weighted patch selection.
- [s4] DER++-style penalty loss included in the final FLAVA objective.
- ... 2 more
Datasets:
- [s5] VGGSound.
- [s5] AudioSet.
- [s8] VGGSound continual split: 8 tasks including sports, music, vehicle, people, animals, home&nature, and two others groups.
- [s8] AudioSet continual split: 7 tasks based on class hierarchy.
- [s8] AVE dataset is used for audiovisual event localization and sound source localization analyses.
Baselines:
- [s2] TVLT and CAV are discussed as audiovisual masked modeling references.
- [s5] ER.
- [s5] MIR.
- [s5] DER++.
- [s5] GMED.
- [s5] CLS-ER.
- [s5] LUMP.
- [s5] Finetune and Multitask are used as lower-bound and upper-bound comparisons.
- ... 1 more
Ablations:
- [s6] Patch-selection ablation: Random, MATS, LAVA-only, FRS-only, and full FLAVA.
- [s8] Rehearsal memory size variation.
- [s8] Audio patch selection variation including time-chunk sizes and frequency/no-constraint alternatives.
- [s8] Pre-training without MAE objective.
- [s8] Shuffled task-order experiments on VGGSound and AudioSet.
- [s8] Sampling-ratio tuning for audio and video patches.
- [s8] AVM temperature tuning.
- [s8] Modality-gap analysis for LAVA and FRS components.
Metrics:
- [s5] Average accuracy, defined as final average performance across tasks.
- [s5] Average forgetting, defined as the average gap between best earlier task performance and final performance.
- [s5] R@K for zero-shot audio-to-video and video-to-audio retrieval.
- [s5] Classification accuracy on VGGSound.
- [s5] mAP on AudioSet classification.
- [s5] GPU memory occupancy and throughput.
- [s6] Modality gap between audio and video embedding clusters.
Results:
- [s6] VGGSound retrieval: FLAVA and FLAVA+ improve average audio-to-video scores by 1.52%p and 2.80%p over baselines.
- [s6] VGGSound retrieval: FLAVA and FLAVA+ improve average video-to-audio scores by 1.80%p and 3.26%p over baselines.
- [s6] AudioSet retrieval: FLAVA and FLAVA+ report average audio-to-video gains of 0.03%p and 2.94%p.
- [s6] AudioSet retrieval: FLAVA and FLAVA+ report average video-to-audio gains of 0.58%p and 3.76%p.
- [s6] Efficiency: FLAVA reports 17.45 GB GPU memory and 17.43 samples/sec throughput in Table 2.
- [s6] Classification: FLAVA and FLAVA+ report higher average classification scores than listed continual learning baselines on VGGSound and AudioSet.
- [s6] Ablation: full FLAVA reports 14.16 audio-to-video average and 14.07 video-to-audio average on VGGSound retrieval in Table 3.
- [s8] AVE event localization: FLAVA and FLAVA+ report 56.68 accuracy.
Stated limitations:
- [s8] In sound source localization, the paper states that all methods fail to accurately pinpoint exact locations of sound sources.
- [s8] The paper attributes sound source localization limitations mainly to the backbone model and states that the backbone has restricted potential for audiovisual parsing and segmentation downstream tasks.
- [s8] The appendix organization notes that Appendix K outlines limitations of the study.
```

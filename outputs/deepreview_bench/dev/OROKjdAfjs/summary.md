# Paper Map

```text
PAPER MAP
Title: TransNormerLLM: A Faster and Better Large Language Model with Improved TransNormer
Authors: Anonymous authors
Venue: ICLR 2024
Submission date: 2023-07-27

SECTIONS
[s1] Abstract and Introduction
Summary: The paper introduces TransNormerLLM, a linear attention-based LLM derived from TransNormer. It identifies quadratic softmax attention cost and weaker practical performance of prior efficient sequence models as motivations, and claims improved accuracy and efficiency through architectural and systems changes.
Key items:
- problem: Conventional Transformer attention has quadratic time complexity in sequence length during training and inference.
- claim: TransNormerLLM is presented as a linear attention-based LLM that surpasses conventional softmax attention in accuracy and efficiency.
- method_component: Main modifications include LRPE with exponential decay, Lightning Attention, gating, SimpleRMSNorm, robust inference, and model parallelism.
- dataset: Models are trained on a self-collected corpus over 6TB with more than 2 trillion tokens.
- result: Benchmark models are trained at 385M, 1B, and 7B parameters, with configurations also described up to 175B parameters.

[s2] Related Work
Summary: This section surveys Transformer-based LLMs and non-Transformer candidates for efficient sequence modeling. It covers linear transformers, state space models, long convolution models, and linear RNNs such as RWKV.
Key items:
- baseline: Transformer-based LLMs discussed include GPT-3, Gopher, PaLM, GLM, Chinchilla, LLaMA, BLOOM, OPT, Pythia, and Falcon.
- other: Linear Transformer methods use hidden-representation decompositions of softmax attention and the right product trick.
- stated_limitation: Most linear transformers are described as having a performance gap compared to traditional Transformers and low practical causal-attention efficiency due to cumulative-sum operations.
- stated_limitation: Long convolution models are described as requiring cached historical computations for causal inference and having higher inference complexity than RNNs.
- baseline: RWKV is cited as a linear RNN-based LLM with competitive performance against similarly scaled GPT models.

[s3] TransNormerLLM Architecture Improvement
Summary: This section details architectural changes to TransNormer, including LRPE-d positional encoding, gated linear attention, Simple GLU, and SimpleRMSNorm. It defines the overall PreNorm-style block with GLA for token mixing and SGLU for channel mixing.
Key items:
- method_component (Equations 1-2): LRPE-d combines linearized relative positional encoding with exponential decay to address dilution while retaining global interactions.
- method_component (Equations 3-4): Gated Linear Attention computes normalized linear attention output multiplied by a gate U.
- method_component (Table 6): Swish is selected as the activation for Q and K in GLA after activation-function ablations.
- method_component (Equation 5): Simple GLU removes the activation function from the channel-mixing GLU.
- method_component (Equation 8): SimpleRMSNorm normalizes by the L2 norm divided by the square root of hidden dimension.
- method_component (Figure 1, Equation 9): Each block applies GLA and SGLU with SRMSNorm in a residual PreNorm structure.

[s4] Training Optimization, Model Parallelism, and Robust Inference
Summary: This section introduces Lightning Attention for IO-aware linear-attention training, system optimizations including FSDP, activation checkpointing, AMP, and model parallelism, and a robust recurrent inference algorithm. It explains how inference avoids numerical precision issues from exponential decay factors.
Key items:
- method_component (Equation 10, Appendix B, Algorithms 3-4): Lightning Attention splits Q, K, and V into blocks and computes masked linear attention using SRAM to reduce HBM traffic.
- method_component: The training system uses FSDP, activation checkpointing, BFloat16 AMP, and model parallelism tailored to SGLU and GLA.
- method_component (Equations 11-13): SGLU model parallelism splits Wv and Wu by columns and Wo by rows, requiring one all-reduce in forward and backward passes.
- method_component (Equations 14-15): GLA model parallelism splits QKVU projections and output computation across devices.
- stated_limitation (Algorithm 1, Equation 17): The original inference form can create numerical precision issues because decay factors shrink query norms and enlarge key norms over time.
- method_component (Algorithm 2, Appendix C): The robust inference algorithm updates a decayed KV state recurrently and produces equivalent outputs without explicit growing inverse decay factors.

[s5] Experiments Setup and Architecture Ablations
Summary: This section describes implementation and pretraining settings and reports ablations for architecture choices. Ablations compare TransNormerLLM with Transformer and TransNormer, positional encodings, decay temperature, gating, activations, normalization functions, SRMSNorm implementation, Lightning Attention, and inference behavior.
Key items:
- dataset: Ablation models are trained on a 300B-token sampled corpus; benchmark models use 1T, 1.2T, and 1.4T tokens for 385M, 1B, and 7B models.
- metric: Ablations report average loss and perplexity over the last 1k iterations.
- result (Table 1): TransNormerLLM outperforms Transformer under identical configurations at 385M and 1B, with reported improvements of 5% and 9%.
- ablation (Table 3): Positional encoding ablation compares Mix, APE, Exp-Decay, LRPE, and LRPE-d; LRPE-d has the lowest perplexity, while Mix is selected for speed.
- ablation (Tables 5-8): Gate, GLA activation, GLU activation, and normalization ablations test gating, Swish/no activation/1+elu, SGLU without activation, and SRMSNorm/RMSNorm/LayerNorm.
- result (Figure 3): Lightning Attention is reported at least 2x faster than PyTorch NormAttention and up to 4x more memory efficient at sequence length 8192.

[s6] Benchmarks and Scaling Experiments
Summary: This section evaluates 385M, 1B, and 7B TransNormerLLM models on commonsense reasoning and aggregated English and Chinese benchmarks. It also discusses scaling experiments and points to appendix results for model parallelism and stress tests up to 175B parameters.
Key items:
- dataset (Table 9): Commonsense benchmarks include BoolQ, PIQA, HellaSwag, WinoGrande, ARC-easy, ARC-challenge, and OpenBookQA.
- dataset (Table 9): Aggregated benchmarks include MMLU, CMMLU, and C-Eval.
- baseline (Table 9): Compared models include OPT, Pythia, BLOOM, GPT-Neo, GPT-J, MPT, Falcon, LLaMA1/2, OpenLLaMA, Baichuan1/2, ChatGLM1/2, and RWKV.
- metric: Commonsense tasks are evaluated in 0-shot with LM-Eval-Harness; MMLU, CMMLU, and C-Eval use 5-shot official scripts.
- result (Table 9): The 7B TransNormerLLM reports 75.87 BoolQ, 80.09 PIQA, 75.21 HellaSwag, 63.40 OpenBookQA, 43.10 MMLU, 47.99 CMMLU, and 43.18 C-Eval.
- result (Section 4.2): The paper states that models remain competitive with open-source Transformer and RWKV baselines at similar scales.

[s7] Appendix: Model Variants, Corpus, and Additional Experimental Results
Summary: The appendix lists model configurations from 385M to 175B parameters, Lightning Attention algorithms, the proof of robust inference equivalence, corpus construction, tokenization, and additional scaling results. It provides training-speed, memory, and context-length comparisons for Transformer and TransNormerLLM.
Key items:
- method_component (Table 10): Model variants are specified for 385M, 1B, 3B, 7B, 13B, 65B, and 175B sizes.
- dataset (Appendix D, Table 11): The corpus is built from over 700TB of public internet text and cleaned to 6TB with 2026B tokens.
- method_component (Figure 5): Data preprocessing includes rule-based filtering, deduplication with MinHash and LSH, and an iterative self-cleaning scheme using a 385M evaluation model and human evaluation.
- method_component (Appendix D.2): Tokenization uses BPE with added Chinese characters and UTF-8 fallback for out-of-vocabulary items.
- result (Table 12): With model parallel size 8, TransNormerLLM-7B reports 24.1GB memory per GPU and 24280 tokens/s, compared with Transformer-7B at 28.7GB and 19973.6 tokens/s.
- result (Tables 13-14): Stress tests report higher tokens/sec/GPU and longer maximum context lengths for TransNormerLLM than Transformer across 7B, 13B, 65B, and 175B sizes.

[s8] Conclusion
Summary: The conclusion restates TransNormerLLM as an improved TransNormer tailored for LLMs. It summarizes that ablations support the chosen modifications and that 385M, 1B, and 7B models match leading Transformer-based LLM performance while having faster inference speeds.
Key items:
- claim: TransNormerLLM consistently outperforms Transformers in both accuracy and efficiency.
- claim: Ablations demonstrate the effectiveness of position encoding, gating, activation choices, normalization, and Lightning Attention.
- result: Benchmark results for 385M, 1B, and 7B models are summarized as matching current Transformer-based LLMs while providing faster inference speeds.
- other: The authors state that they will release pretrained TransNormerLLM models.

GLOBAL INDEX
Claims:
- [s1] TransNormerLLM is claimed to be the first linear attention-based LLM outperforming conventional softmax attention-based models in accuracy and efficiency.
- [s1] The model is claimed to match state-of-the-art Transformer-based LLMs at similar sizes while being faster.
- [s5] TransNormerLLM is reported to outperform a Transformer by 5% at 385M and 9% at 1B under identical configurations.
- [s8] The conclusion claims TransNormerLLM consistently outperforms Transformers in accuracy and efficiency.
Method components:
- [s3] LRPE-d positional encoding with exponential decay.
- [s3] Gated Linear Attention for token mixing with Swish activation.
- [s3] Simple GLU for channel mixing without activation.
- [s3] SimpleRMSNorm normalization.
- [s4] Lightning Attention IO-aware blockwise training algorithm.
- [s4] Robust recurrent inference algorithm for stable linear-attention decoding.
- [s4] FSDP, activation checkpointing, BFloat16 AMP, and model parallelism for SGLU and GLA.
- [s7] BPE tokenization with Chinese vocabulary additions and UTF-8 fallback.
Datasets:
- [s1] Self-collected pretraining corpus over 6TB and more than 2 trillion tokens.
- [s5] 300B-token sampled corpus used for ablation studies.
- [s6] Commonsense reasoning benchmarks: BoolQ, PIQA, HellaSwag, WinoGrande, ARC-e, ARC-c, and OpenBookQA.
- [s6] Aggregated benchmarks: MMLU, CMMLU, and C-Eval.
- [s7] Corpus categories include academic writings, books, code, encyclopedia, filtered webpages, and others.
Baselines:
- [s2] Transformer-based LLMs including GPT-3, Gopher, PaLM, GLM, Chinchilla, LLaMA, BLOOM, OPT, Pythia, and Falcon.
- [s2] Non-Transformer-related models including linear transformers, state space models, long convolution models, and RWKV.
- [s5] Transformer and original TransNormer are used as architecture baselines.
- [s5] APE, Exp-Decay, LRPE, LRPE-d, and Mix are compared as positional encoding variants.
- [s6] Benchmark baselines include OPT, Pythia, BLOOM, GPT-Neo, GPT-J, RWKV, MPT, Falcon, Baichuan, ChatGLM, OpenLLaMA, and LLaMA.
- [s7] Transformer with Flash Attention is compared against TransNormerLLM in model parallelism and stress tests.
Ablations:
- [s5] Transformer vs TransNormerLLM at 385M and 1B.
- [s5] Original TransNormer vs TransNormerLLM at about 385M.
- [s5] Positional encoding ablation over Mix, APE, Exp-Decay, LRPE, and LRPE-d.
- [s5] Decay temperature ablation with and without temperature.
- [s5] Gating mechanism ablation with and without gate.
- [s5] Activation and normalization ablations for GLA, GLU, SRMSNorm, RMSNorm, and LayerNorm.
- [s5] Lightning Attention speed and memory comparison against PyTorch NormAttention.
Metrics:
- [s5] Loss and perplexity averaged over the last 1k iterations.
- [s5] Runtime in milliseconds for forward and backward passes.
- [s5] Memory footprint during training and inference.
- [s6] Benchmark task accuracy or score on BoolQ, PIQA, HellaSwag, WinoGrande, ARC-e, ARC-c, OpenBookQA, MMLU, CMMLU, and C-Eval.
- [s7] Tokens/sec, tokens/sec/GPU, allocated memory per GPU, relative speed, and maximum context length.
Results:
- [s5] TransNormerLLM 385M reports loss 2.248 and PPL 4.770 after 100K updates, compared with Transformer loss 2.362 and PPL 5.160.
- [s5] TransNormerLLM 1B reports loss 1.896 and PPL 3.729 after 100K updates, compared with Transformer loss 2.061 and PPL 4.765.
- [s5] LRPE-d reports loss 2.236 and PPL 4.728, while Mix reports loss 2.248 and PPL 4.770.
- [s5] Lightning Attention is reported at least 2x faster and up to 4x more memory efficient than the PyTorch NormAttention baseline.
- [s6] The 7B model reports 43.10 MMLU, 47.99 CMMLU, and 43.18 C-Eval.
- [s7] TransNormerLLM has higher tokens/sec/GPU than Transformer at 7B, 13B, 65B, and 175B in fixed-context stress tests.
- [s7] TransNormerLLM reaches longer context lengths than Transformer across 7B, 13B, 65B, and 175B under the reported 64 A100 setup.
Stated limitations:
- [s2] Prior efficient sequence modeling methods are said to often have unsatisfactory language-modeling performance and lack real-world speed advantages for LLMs.
- [s2] Linear Transformer causal attention is said to be inefficient in practice due to cumulative-sum operations.
- [s2] Most Linear Transformers are said to have a performance gap compared to traditional Transformers.
- [s2] Long convolution models are said to need cached historical computations for causal inference and have higher inference complexity than RNNs.
- [s3] Learnable lambda in the decay is said to make gradients unstable and lead to NaN values.
- [s5] Using 1+elu in the 7B model may encounter a NaN problem, so Swish is used.
- [s4] The original inference algorithm can suffer numerical precision issues due to decay-related norm shrinkage and growth.
```

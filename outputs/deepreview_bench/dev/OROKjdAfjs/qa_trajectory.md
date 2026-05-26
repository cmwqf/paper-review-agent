# Q&A Trajectory

## Contribution

### Q1

**Question:** How novel are the main claimed components of TransNormerLLM relative to prior work such as TransNormer, RWKV/linear RNNs, RetNet, FlashAttention-style blockwise kernels, RMSNorm/GLU variants, and existing linear-attention LLMs? Please distinguish which contributions are genuinely new versus adaptations/engineering combinations.

**Answer:** The main contribution appears to be an engineering-oriented adaptation of TransNormer-style linear attention into a reasonably scaled LLM system, rather than a set of fundamentally new modeling primitives. The genuinely more novel parts are the specific combination of TransNormer-derived linear attention with exponential-decay positional bias, gating, a numerically stable recurrent inference formulation, and an IO-aware blockwise implementation called Lightning Attention, demonstrated at 385M/1B/7B scale. However, most individual components are adaptations of existing ideas: the architecture is explicitly an improved TransNormer; linear recurrent/linear-attention sequence modeling was already explored by Linear Transformers, RWKV, RetNet-like retention mechanisms, and other efficient sequence models; exponential decay or retention-style temporal weighting is not by itself new; FlashAttention had already established the idea of SRAM/HBM-aware blockwise attention kernels; RMSNorm and GLU/SwiGLU-style feed-forward variants are established Transformer/LLM components; and model parallelism, FSDP, activation checkpointing, AMP, and bfloat16 are standard large-model engineering tools. Thus, the paper’s strongest contribution is not conceptual novelty but a practical recipe showing that a linear-attention/TransNormer variant can be trained and benchmarked as an LLM with competitive speed and accuracy. The novelty claim that it is the “first linear attention-based LLM outperforming conventional softmax attention-based models” should be treated cautiously: the paper compares to RWKV and many Transformer LLMs empirically, but the components themselves mostly derive from prior methods, and without external retrieval in this QA run I cannot fully verify the historical priority of all competing linear-attention LLMs.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper itself positions TransNormerLLM as an “improved TransNormer” and lists the main changes as LRPE with exponential decay, Lightning Attention, gating, SimpleRMSNorm, robust inference, and model parallelism. This indicates that the base architecture is not introduced from scratch but derived from TransNormer.
- paper: The related-work section, according to the provided paper map, explicitly discusses prior Linear Transformers, state-space models, long convolution models, and RWKV as efficient sequence-modeling alternatives, and states that RWKV is a linear-RNN-based LLM with competitive performance. This weakens any claim that linear recurrent/linear-attention LLMs are wholly new.
- paper: The architecture section defines LRPE-d, Gated Linear Attention, Simple GLU, and SimpleRMSNorm. The paper’s ablations test positional encodings, gating, activation functions, GLU activation removal, and RMSNorm/LayerNorm/SimpleRMSNorm variants, suggesting contribution in selecting and combining variants rather than inventing entirely new families of mechanisms.
- paper: The systems section introduces Lightning Attention as a blockwise IO-aware algorithm for linear attention and separately describes FSDP, activation checkpointing, bfloat16 AMP, and model parallelism for SGLU and GLA. The latter are clearly standard engineering adaptations; Lightning Attention is more specific to the paper, but conceptually resembles the established FlashAttention strategy of exploiting blockwise SRAM computation to reduce HBM traffic.
- paper: The robust inference algorithm is motivated by numerical precision issues in the original decay-based recurrence, where decay factors shrink query norms and enlarge key norms over time. This appears to be a more paper-specific technical contribution: an equivalent recurrent formulation that avoids explicit unstable inverse decay factors.
- paper: The experimental sections report that TransNormerLLM outperforms Transformer baselines under identical configurations at 385M and 1B, compares against RWKV and many open-source Transformer LLMs at 7B, and reports speed/memory gains. These results support practical impact, but they do not by themselves establish conceptual novelty of the individual components.
- retrieval: No external scholarly retrieval results were available in this QA run. Therefore, prior-work comparisons to RetNet, FlashAttention, RMSNorm, GLU/SwiGLU, RWKV, and other linear-attention LLMs are based on the paper’s own related-work positioning plus reviewer knowledge, not on newly retrieved bibliographic evidence.
- inference: Component-level novelty assessment: LRPE-d with exponential decay is a modest adaptation of relative/linear positional encoding and retention/decay ideas; Gated Linear Attention is an adaptation of gated linear-attention/RNN-style token mixing; Simple GLU and SimpleRMSNorm are minor simplifications of existing GLU and RMSNorm families; Lightning Attention is a useful implementation contribution but conceptually follows FlashAttention-style IO-aware blocking; robust recurrent inference is one of the more distinct paper-specific contributions; the full LLM-scale integration and empirical recipe are the main contribution.

## Soundness

### Q1

**Question:** Are the main benchmark comparisons against Transformer-based LLMs controlled for training data, token budget, model size, and evaluation protocol, or are they mostly comparisons to externally trained open-source models? In particular, is there a strong same-data/same-compute Transformer baseline at 7B supporting the claim that TransNormerLLM outperforms softmax Transformers in accuracy and efficiency?

**Answer:** The main 7B benchmark comparisons appear to be mostly against externally trained open-source models, not controlled same-data/same-compute Transformer baselines. The paper does include controlled architecture ablations against a Transformer, but only at 385M and 1B, using loss/perplexity after 100K updates on a sampled 300B-token corpus. For the main 7B benchmark table, the baselines are models such as OPT, Pythia, BLOOM, GPT-Neo/J, MPT, Falcon, LLaMA/OpenLLaMA, Baichuan, ChatGLM, and RWKV, which differ in pretraining data, tokenizers, token budgets, training compute, and sometimes training objectives. Although the evaluation protocol is stated for the benchmark tasks, that does not control the pretraining conditions. The appendix provides 7B efficiency comparisons to a Transformer/FlashAttention-style baseline in terms of memory and throughput, but this is not paired with a 7B same-data Transformer accuracy benchmark trained under the same pretraining budget. Therefore, the claim that TransNormerLLM outperforms softmax Transformers in both accuracy and efficiency at 7B is not strongly supported by a controlled same-scale Transformer baseline; the strongest controlled evidence is at smaller scales, while the headline 7B accuracy comparisons are largely external-model comparisons.

**Impact:** weakness, C3, confidence=high

**Evidence:**
- paper: The paper summary reports that ablation models are trained on a 300B-token sampled corpus and that Table 1 compares TransNormerLLM with Transformer under identical configurations only at 385M and 1B, showing lower loss/perplexity for TransNormerLLM.
- paper: The main benchmark section/Table 9 compares TransNormerLLM to many open-source models, including OPT, Pythia, BLOOM, GPT-Neo, GPT-J, MPT, Falcon, LLaMA/OpenLLaMA, Baichuan, ChatGLM, and RWKV, with evaluation on commonsense benchmarks, MMLU, CMMLU, and C-Eval.
- paper: The benchmark protocol is specified as 0-shot LM-Eval-Harness for commonsense tasks and 5-shot official scripts for MMLU/CMMLU/C-Eval, but the listed baselines are not described as retrained on the same corpus, token budget, tokenizer, or compute budget as TransNormerLLM.
- paper: The appendix reports efficiency comparisons for TransNormerLLM-7B versus Transformer-7B, e.g. lower memory per GPU and higher tokens/s, but these speed/memory tests do not provide matching 7B benchmark accuracy for a same-data Transformer.
- inference: Because the controlled Transformer comparison stops at 1B for accuracy/perplexity, and the 7B accuracy comparisons use heterogeneous external baselines, the paper does not isolate the architectural effect of replacing softmax attention with TransNormerLLM at 7B.

### Q2

**Question:** Are the reported efficiency gains, especially the “faster inference” and long-context claims, measured against strong optimized Transformer baselines such as FlashAttention with comparable hardware, batch/context settings, and implementation maturity? Do the experiments separately report prefill/training throughput versus autoregressive decoding speed?

**Answer:** The evidence suggests the efficiency evaluation is only partially sound. The paper does compare against a Transformer baseline in appendix efficiency/stress tests, and the summary indicates that this Transformer uses Flash Attention for some model-parallelism and stress-test comparisons. However, the reported metrics appear to emphasize training throughput and memory under fixed-context stress settings, e.g. tokens/sec/GPU with context length fixed at 2048 and batch size increased until maximum speed before OOM. This is not the same as a careful inference benchmark against an optimized Transformer stack under matched batch size, sequence length, prefill length, decode length, KV-cache behavior, and kernel maturity. The available searched text did not find explicit reporting of “prefill” versus “decoding” throughput, nor a direct “FlashAttention inference” comparison. Thus, the paper's broad “faster inference” and long-context efficiency claims are under-supported: training/prefill-like throughput and maximum-context stress tests do not establish faster autoregressive decoding in realistic serving conditions.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper summary reports appendix efficiency results such as Table 12: TransNormerLLM-7B with model parallel size 8 has 24.1GB memory/GPU and 24280 tokens/s versus Transformer-7B at 28.7GB and 19973.6 tokens/s.
- paper: The paper summary reports Tables 13-14 as stress tests showing higher tokens/sec/GPU and longer maximum context lengths for TransNormerLLM than Transformer across 7B, 13B, 65B, and 175B sizes.
- paper: The available search result for “tokens/sec” shows Table 13 is titled “Efficiency of training models with different sizes” and states: “we keep the context length fixed at 2048 and increased the batch size for both transformer and TransNormerLLM to achieve their maximum speeds without encountering out-of-memory issues.”
- paper: A targeted search for “Flash Attention tokens/sec inference context length decoding prefill” returned no matches, which suggests the paper text does not explicitly present a matched FlashAttention inference/prefill/decoding breakdown under those terms.
- inference: Because autoregressive decoding speed depends heavily on batch size, prompt/prefill length, generated-token length, KV-cache implementation, kernel optimization, and serving setup, training tokens/sec/GPU and maximum-context stress tests are insufficient to substantiate a general “faster inference” claim.

### Q3

**Question:** Do the architecture ablations and reported accuracy gains include repeated runs, variance/error bars, or significance tests, and do they isolate each claimed component at meaningful scale? In particular, are the 385M/1B Transformer-vs-TransNormerLLM improvements based on single runs using last-1k-iteration loss/perplexity, and are the LRPE/gating/SGLU/SRMSNorm/activation ablations controlled for parameter count, compute, and training stability?

**Answer:** No. The reported architecture gains appear to be based on single training runs and summarized by average training loss/perplexity over the last 1k iterations, with no reported repeated seeds, variance/error bars, confidence intervals, or significance tests. This makes the 385M/1B Transformer-vs-TransNormerLLM improvements suggestive but not statistically well-supported. The component ablations do test several claimed changes—positional encoding/LRPE-d, gating, GLA activations, SGLU activations, and SRMSNorm—but they are mostly reported as point estimates of loss/PPL, not as controlled experiments with matched parameter count, matched compute, or systematic stability accounting. Some ablations are at meaningful small/medium LLM scale, especially around 385M and sometimes 1B, but the paper does not demonstrate that each claimed component independently improves performance under parameter- and compute-controlled conditions. Training stability issues are mentioned for some choices, such as learnable decay causing NaNs and 1+elu creating NaN problems at 7B, but these are not analyzed statistically or systematically. For soundness, this weakens the causal interpretation of the architecture ablations and the strength of the reported Transformer-vs-TransNormerLLM accuracy claims.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: The experiment summary states that ablation models are trained on a 300B-token sampled corpus and that ablations report average loss and perplexity over the last 1k iterations. Table 1 reports TransNormerLLM outperforming Transformer at 385M and 1B, e.g. 385M loss/PPL 2.248/4.770 versus Transformer 2.362/5.160, and 1B loss/PPL 1.896/3.729 versus Transformer 2.061/4.765.
- paper: The architecture ablation section reports point-estimate comparisons for positional encodings, decay temperature, gating, GLA activation, GLU/SGLU activation, normalization, SRMSNorm implementation, and Lightning Attention speed/memory. The provided summary does not indicate any repeated runs, standard deviations, error bars, confidence intervals, or hypothesis tests for these tables.
- paper: The paper notes training-stability concerns for some architectural choices: learnable lambda in the decay is said to make gradients unstable and lead to NaN values, and use of 1+elu in the 7B model may encounter NaN problems, motivating Swish. These stability observations are qualitative rather than integrated into controlled statistical ablations.
- inference: Because the comparisons are reported as single point estimates using last-1k-iteration loss/PPL, the architectural gains may reflect run-to-run variation, optimization behavior, or differences in parameterization/compute rather than only the claimed components. The evidence supports a methodological weakness rather than a definitive invalidation of the results.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall / ICLR format (pp. 1–8):**
  - Uses recognizable ICLR style with header, page numbers, section typography, and readable body text.
  - Visually inspectable, but pages are quite dense; several pages have little whitespace, making quick review harder.
  - No obvious cropping, margin overflow, or broken rendering in the provided pages.

- **Figures:**
  - **Figure 1 (p. 4):** Architecture diagram is generally legible and visually connected to the surrounding text. Some internal labels/arrows are small; readability would improve if enlarged or given more horizontal space.
  - **Figures 2–4 (p. 8):** Multi-panel plots are understandable, and captions explain what each panel shows. However, axis labels, tick labels, and legends are quite small, especially in Figure 2’s four subplots. These may be difficult to read in print or at standard PDF zoom.
  - Plot colors/markers are distinguishable, but reliance on small legends and fine gridlines reduces clarity.

- **Tables:**
  - **Tables 1–2 (p. 6):** Mostly legible, but Table 2 is cramped at the bottom/right and visually close to surrounding text. The layout feels compressed.
  - **Tables 3–8 (p. 7):** Tables are readable but small and densely packed in a two-column-like arrangement within the page. Captions are informative, but the page is visually crowded.
  - Table captions usually state the experimental comparison clearly and are connected to nearby explanatory text.

- **Captions:**
  - Captions are generally informative and describe the purpose of each figure/table.
  - **Figures 2–4 (p. 8):** Captions are detailed and help interpret panels; however, long captions plus small plots make the page feel heavy.
  - **Tables 3–8 (p. 7):** Captions are concise and relevant, though several are very close together, reducing visual separation.

- **Equations / algorithms:**
  - Equations throughout pp. 3–6 are well aligned and numbered consistently.
  - **Algorithms 1–2 (p. 6):** Side-by-side layout is legible but compact. The algorithm blocks are visually clear, though the top placement creates a dense start to the page.
  - Mathematical notation appears consistently formatted; no obvious equation overflow.

- **Layout / typography issues:**
  - **p. 4:** Figure 1 is placed beside text, causing a narrow text column and a somewhat cramped layout.
  - **p. 6:** Bottom area is crowded with Table 1, Table 2, and paragraph text; visual hierarchy is less clean here.
  - **p. 7:** Many small tables and paragraphs packed together; difficult to scan quickly.
  - **p. 8:** Three figure groups on one page make the plots small; consider spreading across pages or enlarging key plots.
  - Minor spacing issue visible on **p. 8**: “MMLU(Hendrycks...” lacks a space before the parenthesis.

- **Ease of visual inspection:**
  - The paper is generally readable as an ICLR submission, with standard formatting and clear sectioning.
  - Main weakness is density: figures/tables are present and connected to text, but several visuals are small or crowded, especially pp. 7–8. Enlarging plots/tables or reducing the number of visuals per page would improve reviewability.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

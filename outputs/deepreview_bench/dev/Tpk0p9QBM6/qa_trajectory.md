# Q&A Trajectory

## Contribution

### Q1

**Question:** What are the closest prior works to ARIMEC (especially TIMEC, FIMEC, MEME, and any prefix-tree/autoregressive coupling or steganography methods), and in what concrete ways is this paper's method technically novel rather than a straightforward recombination of those ideas?

**Answer:** The closest prior works are the paper’s own IMEC predecessors: TIMEC, which handles an autoregressive distribution over Y but requires a tabular posterior over X; FIMEC, which scales by assuming X factorizes into independent components; and MEME/Markov-coding-game work, which uses IMEC-style low-entropy couplings for communication but apparently with a uniform-token/FIMEC-style message model. Classical MEC approximation algorithms are also relevant, but they target explicit finite supports and scale roughly log-linearly in support size, rather than addressing huge autoregressive supports. For steganography, the closest conceptual prior is coupling-based or arithmetic-coding-style distribution matching: encode messages into covertext while preserving the covertext distribution. The paper’s novelty is not that it invents MEC, IMEC, autoregressive sampling, or prefix trees in isolation. The concrete technical contribution is narrower: it formulates IMEC as selection over a set of partitions, shows TIMEC and FIMEC are special cases, and instantiates the partition family with prefix-tree partitions so that arbitrary discrete/autoregressive message distributions can be coupled without requiring a fully tabular X distribution or an independent-factor X distribution. It further adds implementation machinery—lazy posterior updates and entropy upper-bound pruning—to search these prefix-tree partitions more efficiently.

**Impact:** strength, C2, confidence=medium

**Evidence:**
- paper: The paper’s background presents TIMEC as iteratively coupling a posterior over X with the next autoregressive component of Y, with runtime depending on the explicit support size of X. This makes TIMEC a direct predecessor but limited when X has very large support.
- paper: The paper presents FIMEC as an efficient IMEC variant under the assumption that X has independent components, selecting the maximum-posterior-entropy component to couple with the next component of Y. This is close prior work but does not handle arbitrary non-factorable distributions over X.
- paper: The paper’s Section 3 claims a unification: generic IMEC is parameterized by a set of partitions over X, and TIMEC/FIMEC are recovered by particular partition choices. This is a genuine conceptual contribution relative to treating TIMEC and FIMEC as separate algorithms.
- paper: The paper defines ARIMEC as generic IMEC with a prefix-tree partition set: one partition per node in the prefix tree of X’s support. This is the main technical novelty relative to TIMEC/FIMEC, because it replaces “all support points” or “independent factors” with hierarchical prefix blocks suitable for autoregressive distributions.
- paper: The paper states that ARIMEC uses lazy posterior updates and entropy upper bounds to prune subtree searches. This is an implementation-level contribution needed to make prefix-tree partition search practical, although the paper also acknowledges that the resulting runtime bound is not polynomial in the worst case because naive search can check exponentially many prefix-tree nodes.
- paper: In experiments, the Markov coding game baseline is described as a naive MEME/FIMEC variant assuming a uniform token distribution, while ARIMEC uses the correct autoregressive prior. This suggests the empirical gain is largely from relaxing the uniform/factorized-message assumption rather than from a fundamentally new coding objective.
- inference: As a contribution judgment, ARIMEC is technically more than a trivial recombination if the partition-set abstraction and prefix-tree partition operations are original to this paper. However, the novelty is incremental/moderate rather than sweeping: it combines IMEC’s greedy low-entropy coupling idea with a standard prefix-tree representation for autoregressive supports, and its empirical applications to MEME/steganography largely follow naturally from coupling-based distribution matching.
- retrieval: No external scholarly retrieval results were available in the tool observations, so this assessment relies on the paper’s internal positioning and reviewer judgment rather than independently verified prior-art search.

### Q2

**Question:** How broad is the likely impact of ARIMEC beyond the demonstrated Markov coding game and steganography settings, given its lack of a polynomial-time worst-case guarantee and reliance on prefix-tree search/pruning? Are the claimed application areas plausibly enabled by this method, or is the contribution mainly narrow/empirical?

**Answer:** ARIMEC’s likely near-term impact appears mainly narrow and empirical rather than broadly enabling across the claimed application areas. The paper makes a plausible methodological contribution by extending iterative minimum-entropy coupling to arbitrary autoregressive/discrete distributions via prefix-tree partitions, and it demonstrates useful gains in Markov coding games and steganography. However, the broader claim that this generally enables large-support, non-factorable MEC applications is weakened by the stated runtime dependence on the number of prefix-tree nodes searched and the explicit absence of a polynomial-time worst-case guarantee. The practical success therefore depends on whether entropy-bound pruning is effective for a given distribution, which is shown empirically only in the two evaluated settings. Claimed downstream areas such as entropic causal inference, random number generation, functional representations, and dimensionality reduction are plausible motivations, but the paper does not demonstrate them or establish that ARIMEC will scale reliably there. Thus, the contribution is best viewed as an interesting general heuristic/framework with promising empirical examples, not yet as a broadly validated general-purpose solver for large-support MEC.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper claims ARIMEC is a general approach for arbitrary large-support discrete distributions, using prefix-tree partitions within the IMEC framework.
- paper: Its stated runtime is O(m max(M,N) log max(M,N) + mZN), where Z is the number of prefix-tree nodes checked when searching for the maximum-entropy partition.
- paper: The paper explicitly notes that this bound does not provide a polynomial-time guarantee, because a naive maximum-entropy partition search can require Z = N^n checks.
- paper: The empirical evaluation is limited to Markov coding games and GPT-2-based steganography settings, where ARIMEC is compared mainly against FIMEC/uniform-token baselines and shows improved encoding efficiency or throughput.
- paper: The conclusion lists broader possible applications including entropic causal inference, random number generation, functional representations, and dimensionality reduction, but these are not empirically evaluated.
- inference: Because ARIMEC’s scalability relies on distribution-dependent prefix-tree pruning rather than a worst-case polynomial guarantee, the demonstrated impact does not automatically transfer to substantially different large-support MEC applications.

### Q3

**Question:** Are the empirical contributions and baselines strong enough to support a meaningful contribution claim? In particular, do the Markov coding game and steganography experiments compare ARIMEC against the most relevant alternatives, or are the gains mainly due to using a more accurate autoregressive prior than a weak uniform/FIMEC baseline?

**Answer:** No. The experiments support a narrower contribution claim—that ARIMEC can exploit non-factorized/autoregressive message priors where FIMEC cannot—but they are not strong enough to establish broad empirical superiority. In both the Markov coding game and unencrypted steganography settings, the main comparison is ARIMEC using the correct autoregressive GPT-2-based prior versus a naive FIMEC/MEME-style baseline that assumes a uniform token distribution. That makes the empirical gains difficult to attribute specifically to the ARIMEC coupling procedure rather than to the much better prior model. The paper does show that this is practically useful, because using the richer prior improves encoding/throughput while preserving task performance, but the baseline set is weak for a strong contribution claim: there is no comparison to stronger coding/steganographic methods, no ablation that gives competitors access to comparable prior information, and no clear separation between “better coupling algorithm” and “better distributional assumption.”

**Impact:** weakness, C3, confidence=medium

**Evidence:**
- paper: The paper’s own experiment summary indicates that the Markov coding game experiments compare ARIMEC against a “naive MEME variant assuming a uniform token distribution and using FIMEC,” while ARIMEC uses message distributions from GPT-2 with top-50 sampling. The reported result is that both methods preserve expected return, but ARIMEC gives a more efficient encoding.
- paper: For unencrypted steganography, the reported comparison is again ARIMEC with the correct prior against uniform-token FIMEC, with ARIMEC achieving higher information throughput. This directly supports the concern that the gains may arise from using an accurate autoregressive prior rather than from a stronger algorithmic comparison.
- paper: The information-theoretic steganography results are also not uniformly favorable: the summary states that FIMEC gives lower joint entropy than ARIMEC, while ARIMEC gives lower decoding error. This weakens the claim that ARIMEC is empirically dominant as a low-entropy coupling method.
- inference: Because FIMEC is designed for factored distributions and the evaluated baseline assumes a uniform token distribution, the comparison is partly between different modeling assumptions, not only between coupling algorithms. A stronger empirical contribution would include baselines or ablations that control for prior quality, compare against established language-model steganography/coding methods, or quantify the incremental benefit of ARIMEC’s prefix-tree partitioning over simpler autoregressive coding approaches.
- retrieval: No external scholarly retrieval results were available in the tool observations, so the assessment of “most relevant alternatives” is based on the paper’s stated baselines and reviewer judgment rather than a verified literature search.

## Soundness

### Q1

**Question:** Do the experiments compare ARIMEC against sufficiently strong and appropriate baselines for the claimed applications, especially prior MEC/IMEC methods using the same non-uniform autoregressive priors where feasible, or only against a uniform-token FIMEC/MEME baseline?

**Answer:** No. Based on the experimental description, the comparisons are mainly against a naive FIMEC/MEME-style baseline that assumes a uniform token/message distribution, while ARIMEC is given the correct non-uniform autoregressive prior. The paper does discuss prior MEC/IMEC methods such as TIMEC and FIMEC in the background, but the reported application experiments do not appear to include stronger comparisons using the same autoregressive prior where possible, nor small-scale comparisons to tabular/optimal MEC or prior approximate MEC methods. This makes the empirical evidence weaker: the observed gains may partly reflect correcting a misspecified uniform prior rather than demonstrating that ARIMEC is superior to the strongest feasible low-entropy coupling methods for those applications.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: The paper map for Section 5 states that in Markov coding games, “ARIMEC extends MEME to arbitrary message distributions and is compared with a uniform-token FIMEC baseline,” and identifies the MCG baseline as “a naive MEME variant assuming a uniform token distribution and using FIMEC.”
- paper: The paper map further states that the steganography experiments compare “ARIMEC with the correct autoregressive prior against FIMEC with a uniform-token assumption,” including the unencrypted steganography result where ARIMEC outperforms uniform-token FIMEC in throughput.
- paper: The background section lists relevant prior methods—TIMEC, FIMEC, and provable MEC approximation algorithms—but the experiment summary does not report direct empirical comparisons against these alternatives under matched non-uniform priors or on smaller tractable instances.
- inference: Because the baseline is intentionally mismatched to the true non-uniform autoregressive message prior, the experiments support the claim that using prior information helps, but they do not strongly isolate the benefit of ARIMEC relative to the best feasible prior MEC/IMEC approaches.

### Q2

**Question:** Are the theoretical claims about ARIMEC technically justified—specifically, does the paper prove that ARIMEC always induces a valid coupling for arbitrary discrete autoregressive distributions, and are any optimality or low-entropy guarantees beyond validity clearly limited to heuristic/greedy statements?

**Answer:** Yes, with an important limitation. The paper appears technically justified on the core validity claim: it proves that the generic IMEC procedure induces a coupling of the target marginals, and ARIMEC is defined as a specific instance of that procedure using prefix-tree partitions. Therefore, under the method’s stated assumptions—access to the relevant discrete autoregressive probabilities/support operations and exact implementation of the iterative conditional updates—the coupling-validity claim for ARIMEC follows from the generic IMEC coupling proposition. However, the stronger “low-entropy” or “minimum-entropy” implications are not proved as global guarantees for ARIMEC. The paper’s theoretical support for entropy reduction is framed as heuristic/greedy: IMEC selects a partition with high posterior block entropy, and the only stated optimality-type result is a next-step approximate minimization result when the trivial partition is available, subject to previous choices. That does not establish that ARIMEC finds a minimum-entropy coupling, a constant-factor approximation, or even a globally optimal low-entropy coupling. Thus, the theory is sound for validity but should not be read as proving global optimality.

**Impact:** strength, C2, confidence=medium

**Evidence:**
- paper: Section 3 states a generic IMEC algorithm parameterized by a partition set and includes Proposition 3.1, summarized as proving that IMEC induces a coupling of the specified marginals.
- paper: Section 4 defines ARIMEC as Algorithm 3 instantiated with the prefix-tree partition set, so ARIMEC inherits the generic IMEC coupling-validity result.
- paper: Section 3 describes the selected partition as offering the largest heuristic opportunity for joint entropy reduction, and Proposition 3.2 is limited to approximate next-step joint-entropy minimization subject to previous choices and under the condition that the trivial partition is included.
- paper: Section 4.2 also notes that ARIMEC’s runtime bound is not a polynomial-time guarantee because the search over prefix-tree nodes can be exponential in a naive implementation, reinforcing that the theory is not a global efficient MEC approximation guarantee.
- inference: Because ARIMEC is only an instance of generic IMEC, Proposition 3.1 supports marginal validity, but no cited theorem establishes global minimum-entropy optimality or approximation quality for ARIMEC’s prefix-tree-restricted greedy choices.

### Q3

**Question:** Are the runtime and scalability claims for ARIMEC supported by rigorous analysis and experiments, including whether the number of checked prefix-tree nodes Z is measured or shown to remain manageable in the reported large-support settings?

**Answer:** No. The paper gives a formal runtime expression for ARIMEC, but the scalability claim is only partially supported because the dominant search term depends on Z, the number of prefix-tree nodes checked, and the paper does not appear to empirically measure Z or demonstrate that it remains small in the reported large-support experiments. The analysis explicitly leaves open the possibility of a non-polynomial search cost: ARIMEC is bounded as O(m max(M,N) log max(M,N) + mZN), and the paper notes that a naive implementation can have Z = N^n. Although pruning via entropy upper bounds is proposed, the experimental section mainly reports task outcomes such as decoding error, expected return, joint entropy, and information throughput, not wall-clock runtime, scaling curves, checked-node counts, or ablations isolating the pruning mechanism. Thus, the claim that ARIMEC scales to arbitrary large-support distributions is not rigorously validated experimentally.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: The paper map reports Proposition 4.1: ARIMEC runtime is O(m max(M,N) log max(M,N) + mZN), where Z is the number of prefix-tree nodes checked for maximum entropy.
- paper: The paper map reports a stated limitation in Section 4.2: the runtime bound does not give a polynomial-time guarantee because a naive implementation has Z = N^n.
- paper: The paper map reports that Section 4 proposes lazy posterior updates and entropy upper-bound pruning, but this is an implementation heuristic/optimization rather than a bound showing Z is generally manageable.
- paper: The listed experimental metrics are trajectory decoding error, expected return, joint entropy, ciphertext decoding error, information throughput, and bootstrap confidence intervals; no reported metric in the provided paper map measures Z, node-check counts, wall-clock runtime, or empirical scaling with support/tree size.
- inference: Because the dominant runtime term contains Z and Z may be exponential without further guarantees, scalability claims require either a theoretical bound on Z under relevant assumptions or empirical evidence that Z remains small in the tested settings. The reported experiments do not provide that evidence.

### Q4

**Question:** Do the experiments include sufficient ablations and statistical evidence to isolate ARIMEC’s claimed contributions—for example, effects of prefix-tree partitions, entropy-pruning/lazy updates, use of the correct prior, and variability over more than 100 samples/games?

**Answer:** No. The experimental evidence is useful but not sufficient to isolate ARIMEC’s individual claimed contributions. The paper reports comparisons between ARIMEC using an autoregressive/correct prior and a FIMEC-style baseline assuming a uniform token prior, and it reports 95% bootstrap confidence intervals over 100 games or samples in some figures. However, this comparison conflates several factors: the ARIMEC algorithm, the prefix-tree partition family, and use of the correct prior. The experiments do not appear to separately ablate prefix-tree partitions against alternative partition sets, entropy-bound pruning or lazy posterior updates against naive implementations, or the effect of prior correctness while holding the coupling algorithm fixed. The statistical evidence is also limited: the reported variability is primarily based on 100 games/samples, not more than 100, and there is no clear indication of repeated random seeds, significance tests, or confidence intervals for all claimed throughput/runtime effects. This weakens the soundness of empirical claims that ARIMEC’s specific algorithmic components are responsible for the observed improvements.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The experiments compare ARIMEC with a baseline described as a naive MEME/FIMEC variant assuming a uniform token distribution, while ARIMEC uses autoregressive prior information. This supports a broad method comparison but does not isolate whether gains come from the prefix-tree partition set, the prior, or other implementation details.
- paper: The Markov coding game evaluation reports trajectory decoding error with 95% bootstrap confidence intervals over 100 games, and the steganography evaluation reports joint entropy and decoding error over 100 GPT-2 covertext samples. This provides some uncertainty quantification but only at a relatively small sample count and not clearly beyond 100 samples/games.
- paper: The method section claims practical efficiency mechanisms including lazy posterior updates and entropy upper-bound pruning for prefix-tree search, but the experiment summary does not indicate a dedicated runtime or accuracy ablation comparing these mechanisms against non-lazy or non-pruned variants.
- inference: Because the main empirical baseline changes both the assumed prior and the coupling/partition structure, the experiments cannot causally attribute improvements specifically to ARIMEC’s prefix-tree partition formalism or to correct-prior modeling. More controlled ablations would be needed for strong soundness: e.g., ARIMEC with uniform prior, FIMEC with correct prior where applicable, alternative partition sets, pruning disabled, lazy updates disabled, and larger multi-seed evaluations.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall / ICLR format:** The paper is generally easy to visually inspect: single-column ICLR-style layout, readable body font, clear section hierarchy, page numbers, and anonymous author block.

- **Major formatting concern — excessive blue text (pp. 1, 3–7):** Large portions of normal prose, propositions, assumptions, and notes appear in bright blue, not just citations/links. This is visually distracting and nonstandard for an ICLR submission; it makes some pages look like annotated or hyperlinked drafts rather than final paper text.

- **Figures:**
  - **Figure 1 (p. 5):** Diagram is legible and caption clearly explains left/right components. Some symbols and colored blocks are small but understandable.
  - **Figure 2 (p. 7):** Overall legible, but notation inside the right-hand partition diagram is small and may be hard to read when printed. Caption is informative and well connected.
  - **Figure 3 (p. 7):** Plots are readable, with clear axes and legend. However, tick labels, line-style legend, and confidence bands are somewhat small; the page is visually crowded with two figures plus text.
  - **Figure 4 (p. 8):** Plots are mostly legible; axes and legend are readable. Caption is concise and connected, though it does not describe the two subplots individually.

- **Tables:** No tables are visible in the provided pages.

- **Algorithms / equations:**
  - **Algorithms 1–3 (pp. 3–5):** Algorithm boxes are clean and legible, with good rule separation. Some mathematical subscripts are small but acceptable.
  - **Equation formatting (pp. 2–6):** Display equations are generally readable and aligned well. Dense definitions with heavy notation are visually compact but not malformed.

- **Captions:** Captions are generally informative and tied to the visual content. Figure 3 and Figure 4 captions include experimental context and confidence interval information, which is helpful.

- **Layout / spacing:**
  - **p. 4:** Algorithm 2 starts very high on the page immediately under the top rule; acceptable but slightly abrupt.
  - **p. 7:** The page is visually busy: Figure 2, Figure 3, a long blue proposition, and section heading all appear on one page. Inspection is still possible, but the page feels crowded.
  - **Footnotes (pp. 3–4, 6, 8):** Footnotes are readable, though some are long and visually dense.

- **Typography:** Section headings and small caps are consistent. Body text is readable. The main typography issue is the widespread blue coloring, which reduces visual polish and consistency.

- **Bottom line:** The submission is mostly readable and inspectable, with legible figures/algorithms and useful captions. The most important presentation fix is to remove or greatly reduce the blue text styling so that only actual hyperlinks/citations, if any, are colored.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

### Q2

**Question:** Assess the paper text for organization and writing clarity: are the main contributions, definitions/notation, algorithms, theorem/proposition statements, and experimental narrative easy to follow? Please cite specific sections/pages if possible, and note any ambiguities or terminology issues that affect presentation.

**Answer:** The paper is generally well organized and readable, with a clear progression from motivation and contributions, to definitions and prior algorithms, to the generic IMEC framework, ARIMEC, experiments, and appendices. The main contributions are easy to locate in the Introduction: the paper explicitly frames three contributions—partition-set unification of IMEC, ARIMEC for arbitrary large-support discrete distributions, and empirical demonstrations in Markov coding games and steganography. The definitions and notation in Section 2 are mostly clear: Definitions 2.1--2.3 introduce couplings, entropy, and MEC before the paper moves to TIMEC/FIMEC and partition notation. Algorithms 1--3 appear to be placed close to the relevant explanatory text, which helps the reader follow the transition from existing methods to the proposed generic IMEC abstraction. Proposition statements are also placed in sensible locations: Proposition 3.1 establishes that generic IMEC induces a valid coupling, Proposition 3.2 explains the greedy entropy interpretation, and Proposition 4.1 summarizes ARIMEC runtime.

**Impact:** strength, C2, confidence=medium

**Evidence:**
- paper: Section 1 introduces the MEC problem, motivates large-support distributions, and lists the paper's three main contributions: a partition-set formalism, ARIMEC, and empirical applications. This is a presentation strength because the reader can identify the claimed contribution early.
- paper: Section 2, “Background and Notation,” defines the central objects before using them: couplings and MEC are introduced in Definitions 2.1--2.3; TIMEC and FIMEC are subsequently reviewed with Algorithms 1--2 and runtime propositions. This ordering supports readability.
- paper: Section 3 presents the generic IMEC algorithm using a partition set, then states Proposition 3.1 that the output is a coupling and Proposition 3.2 that inclusion of the trivial partition gives a greedy approximate next-step joint-entropy property. The algorithm/theorem flow is coherent.
- paper: Section 4 defines ARIMEC through prefix-tree partitions, gives the ARIMEC runtime in Proposition 4.1, and discusses implementation ideas such as lazy posterior updates and entropy-bound pruning. This gives the reader both the formal definition and some implementation intuition.
- paper: Section 5 separates the experimental narrative into Markov coding games and steganography settings, and ties results to Figures 3--5. The narrative mostly explains what is measured—decoding error, expected return, joint entropy, and throughput—and why ARIMEC is expected to help.
- inference: The main presentation weakness is terminology density. The paper introduces several closely related objects—partitions, block functions, prefix-tree partitions, posterior block entropy, trivial partitions, TIMEC, FIMEC, IMEC, and ARIMEC—and the distinction between the generic framework and the concrete ARIMEC instantiation may require repeated cross-referencing.
- inference: Another ambiguity is that the phrase “arbitrary large-support distributions” may read stronger than the actual computational guarantee: Section 4.2 notes that the runtime bound depends on the number of tree nodes checked and does not yield a polynomial-time guarantee in the naive case. This affects presentation because the headline wording risks overstating the ease of applying the method.
- inference: The experimental exposition is understandable, but it relies on application-specific terminology from Markov coding games, MEME, steganography, covertext/plaintext priors, and GPT-2 token distributions. Readers outside these areas may need the appendix to fully understand the setups and assumptions.

# Q&A Trajectory

## Contribution

### Q1

**Question:** How novel are the paper’s main contributions relative to prior work on plasticity loss, data augmentation, critic/actor plasticity diagnostics, and replay-ratio scheduling in visual RL? In particular, were the findings that data augmentation preserves plasticity, critic plasticity is the dominant bottleneck, early plasticity loss is hard to recover, or FAU-based Adaptive RR already established or substantially anticipated by prior methods such as Reset, ReDo, primacy bias work, DrQ/DrQ-v2, or high replay-ratio studies?

**Answer:** The paper’s contribution appears moderately novel but substantially incremental. The strongest novelty is not the individual ingredients—data augmentation, plasticity loss, dormant/active-unit diagnostics, reset/recycling interventions, or the high replay-ratio dilemma were all known—but the systematic decomposition in visual actor-critic RL: showing that DrQ-style data augmentation behaves like a plasticity-preserving intervention, that the critic’s FAU/plasticity is more diagnostic than the actor/encoder in their setting, and using critic FAU to trigger a replay-ratio increase. However, several headline conclusions are substantially anticipated by prior work. DrQ/DrQ-v2 had already established that image augmentation is central to sample-efficient visual RL, though not primarily as a plasticity-preservation mechanism. Primacy-bias and Reset-style work already argued that early training can create persistent loss of adaptability and that timely reset/intervention matters. ReDo/dormant-neuron work already connected inactive units/plasticity loss to RL performance and proposed neuron-level recovery mechanisms. High replay-ratio studies had already identified the tradeoff that more gradient updates can improve data reuse but worsen overfitting/plasticity or stability. Thus, the paper’s findings are better viewed as a useful synthesis and targeted empirical clarification in visual RL rather than a wholly new conceptual discovery. The FAU-based Adaptive RR rule is probably the most concrete new method, but it is a simple schedule that is strongly motivated by prior dormant-unit and high-replay-ratio work; its novelty is in using critic FAU as the switching signal rather than in the general idea of adapting update intensity to avoid early plasticity loss.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper positions its own contributions as three empirical findings and one method: data augmentation mitigates plasticity loss, critic plasticity loss is the main bottleneck, early recovery is crucial, and Adaptive RR changes replay ratio based on critic FAU. The provided paper map reports these claims in the Introduction, Modules, Stages, and Methods sections.
- paper: The paper itself compares against or discusses Reset, ReDo, Plasticity Injection, L2-Init, CReLU, DrQ-v2-style augmentation, and static replay-ratio baselines. This indicates that the authors are building directly on an existing plasticity-loss and visual-RL intervention literature rather than introducing the problem or the intervention family from scratch.
- paper: For data augmentation, the paper’s factorial experiment shows that without augmentation Reset helps, while with augmentation Reset gives little or sometimes negative additional benefit. This supports the paper’s specific claim that augmentation can preserve plasticity, but also shows the result is tied to a known DrQ/DrQ-v2 ingredient rather than a new algorithmic mechanism.
- paper: For critic plasticity, the paper uses module-wise FAU and plasticity injection into actor versus critic, reporting that critic FAU changes most with augmentation and that critic injection is more helpful after no-augmentation early training. This module-level diagnostic is a relatively distinctive contribution compared with generic dormant-neuron or Reset results.
- paper: For training stages, the paper turns augmentation on or off at different times and reports that late augmentation after severe early plasticity loss does not recover performance, whereas early augmentation allows recovery. This is a visual-RL-specific ablation of a phenomenon closely related to primacy bias.
- paper: For Adaptive RR, the paper’s method starts with low replay ratio and switches to higher replay ratio when consecutive critic FAU checkpoints stabilize. This is a simple FAU-triggered rule; the paper evaluates it against static low/high RR and reset/recycling baselines on DMC and Atari-100K.
- retrieval: No external scholarly retrieval results were available in the tool observations for this answer, so the prior-work comparison relies on the paper’s own related-work positioning plus reviewer knowledge of the named prior methods. This lowers confidence relative to a fully retrieved literature audit.
- inference: DrQ/DrQ-v2 substantially anticipated the practical importance of image augmentation in visual RL, but not necessarily the plasticity-preservation interpretation. Reset and primacy-bias work substantially anticipated the early-loss/irrecoverability narrative. ReDo and dormant-neuron work anticipated active-unit-style plasticity diagnostics and neuron-level recovery. High replay-ratio work anticipated the low-vs-high update tradeoff. The paper’s incremental novelty is in combining these threads and localizing the bottleneck to the critic in visual actor-critic agents.

## Soundness

### Q1

**Question:** What statistical evidence does the paper provide for its main empirical claims and Adaptive RR results—e.g., number of seeds, error bars/confidence intervals, significance tests, and whether trends hold across all reported DMC tasks and Atari games rather than only selected examples?

**Answer:** The paper provides moderate but not fully rigorous statistical support. Its empirical evidence is mainly learning curves and aggregate tables, with experiments apparently run over multiple random seeds; the appendix specifies 5 random seeds per Atari game, and the paper map indicates additional DMC/Atari appendix results across tasks and seeds. However, the evidence appears to rely on visual curve comparisons and aggregate means/medians rather than formal statistical testing: I do not see evidence of significance tests, p-values, bootstrap confidence intervals, or explicit hypothesis tests for the main plasticity claims or Adaptive RR gains. For Adaptive RR, the DMC evidence is stronger than single-task evidence because Figure 9 evaluates six DMC tasks and reports that Adaptive RR improves sample efficiency over static RR settings on the reported tasks. The Atari evidence is more mixed: Table 2 reports aggregate HNS statistics over 17 Atari-100K games, with Adaptive RR achieving mean HNS 55.8%, median HNS 48.7%, 4 superhuman games, and 11 best scores, which implies it is not best on all 17 games. Earlier diagnostic claims are less uniformly supported across the full benchmark: several motivating analyses are centered on selected DMC tasks such as Cheetah Run, although appendices reportedly broaden some trends. Overall, the paper gives useful multi-seed, multi-task empirical evidence, but the lack of formal uncertainty quantification/significance testing and the fact that some claims are illustrated on selected tasks weaken the statistical soundness of the strongest claims.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper map states that Adaptive RR is evaluated on six challenging DMC continuous-control tasks in Figure 9 and is reported to outperform static low and high replay-ratio settings on those reported DMC tasks.
- paper: For Atari-100K, the paper map reports a 17-game evaluation with 5 random seeds per game and Table 2 aggregate results: mean HNS 55.8%, median HNS 48.7%, 4 superhuman games, and 11 best scores for Adaptive RR.
- paper: The main plasticity analyses include selected-task figures, e.g. intervention comparisons on Cheetah Run, module FAU analyses, and timing ablations, with additional appendix figures said to extend some trends across tasks and seeds.
- inference: Because the reported Atari result has 11 best scores among 17 games, the Adaptive RR improvement does not hold uniformly across every Atari game. The available description also indicates aggregate/visual evidence rather than significance tests or confidence intervals.

### Q2

**Question:** Does the paper include ablations showing that Adaptive RR's FAU-based switching rule is necessary—e.g., comparisons to simple time-based delayed replay-ratio schedules, threshold/check-interval sensitivity, or alternative plasticity metrics—rather than gains coming mainly from starting with a low replay ratio and increasing later?

**Answer:** No. The paper supports Adaptive RR mainly by comparing it to static replay-ratio settings, such as low RR and high RR, and by motivating the switch using critic FAU stabilization. However, it does not appear to include the key ablations needed to establish that the FAU-based switching rule itself is necessary. In particular, the reported evidence does not include a simple time-based delayed schedule that starts with low RR and switches to high RR at a fixed step, sensitivity analysis for the FAU threshold or check interval, or comparisons where alternative plasticity metrics are used as the switching signal. This leaves open the possibility that much of Adaptive RR's gain comes from the coarse schedule of “low RR early, high RR later,” rather than from the specific critic-FAU criterion.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The Adaptive RR method is described as starting with RR=0.5 and switching to RR=2 when consecutive critic FAU checkpoints differ by less than a threshold, reported as 0.001 in the paper map. Algorithm 1 in the appendix specifies a FAU-based check interval and threshold-based switch rule.
- paper: The main evaluations compare Adaptive RR against static replay-ratio baselines, including static low RR and static high RR on DeepMind Control, and static RR/ReDo-style settings on Atari-100K. These comparisons show improved performance but do not isolate whether adaptivity via FAU is better than a predetermined delayed increase.
- paper: The appendix discusses additional plasticity metrics such as feature rank, weight norm, and FAU, but the provided summary indicates these are discussed as diagnostics rather than evaluated as alternative switching criteria for Adaptive RR.
- paper: The limitations state that Adaptive RR is demonstrated only under basic configurations, which is consistent with the absence of more detailed design ablations such as threshold sensitivity, check-interval sensitivity, or alternative switch metrics.
- inference: Because the closest baselines are static RR settings, the experiments establish that Adaptive RR is better than always-low or always-high RR in the tested settings, but they do not rule out the simpler explanation that any delayed low-to-high RR schedule would have achieved similar gains.

### Q3

**Question:** Are the baselines for Adaptive RR sufficiently strong and current on DMC and Atari-100K—especially compared with established sample-efficient visual RL/high-replay methods and simple tuned static replay-ratio variants—or are important baselines missing that would weaken the claim that Adaptive RR effectively resolves the high replay-ratio dilemma?

**Answer:** The Adaptive RR baselines are useful but not fully sufficient to support a strong claim that the method “resolves” the high replay-ratio dilemma. The paper does include relevant internal controls: on DMC it compares Adaptive RR against low and high static replay-ratio settings, and on Atari-100K it compares against several static replay-ratio settings and reset/plasticity baselines such as Reset/ReDo. These are appropriate for testing the paper’s mechanistic hypothesis that delaying high replay until critic FAU stabilizes can avoid early plasticity loss.

However, the comparison set appears narrow relative to the broader sample-efficient visual RL literature. For Atari-100K in particular, the reported Adaptive RR result—mean HNS 55.8%, median HNS 48.7%—is far below the level associated with established modern sample-efficient Atari agents, so the absence of comparisons to strong Atari-100K methods such as SPR/EfficientZero/BBF-style agents limits the strength of the empirical claim. Similarly, on DMC, the paper mainly evaluates Adaptive RR within a DrQ-v2-style setup against static replay-ratio variants, rather than against a broader set of current visual RL methods or high-replay algorithms. The static RR comparison is directionally useful, but it is not clear from the summarized evidence that the authors include a sufficiently tuned grid of simple alternatives—e.g., intermediate static replay ratios, task-tuned static RR, delayed fixed schedules independent of FAU, or matched-update-budget schedules. Such controls would be important because Adaptive RR may benefit from a simple low-then-high schedule rather than specifically from the FAU-based adaptation rule.

Thus, the baselines are adequate for a within-framework proof of concept, but important current and simple-control baselines are missing. This weakens the soundness of broad claims that Adaptive RR generally solves the high replay-ratio dilemma, though it does not invalidate the narrower finding that the proposed schedule improves over the particular static RR and reset baselines tested.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper’s Adaptive RR method starts with a low replay ratio and switches to a higher replay ratio when critic FAU stabilizes; the summarized DMC evaluation compares it primarily against static low RR and static high RR settings.
- paper: For Atari-100K, the paper reports Adaptive RR with mean HNS 55.8%, median HNS 48.7%, 4 superhuman games, and 11 best scores among the compared settings, with baselines including static RR settings and ReDo/Reset-style plasticity interventions.
- paper: The paper’s own limitations state that Adaptive RR is demonstrated only under basic configurations, leaving more nuanced designs for future work.
- inference: Because the Adaptive RR comparison is mostly within the authors’ base agent and against limited static/reset variants, it does not establish competitiveness against the strongest current sample-efficient visual RL agents or rule out simpler tuned replay-ratio schedules.
- inference: The absence of broader Atari-100K and DMC baselines matters especially because the paper frames Adaptive RR as addressing the general high replay-ratio dilemma, not merely improving one DrQ-v2/Rainbow-style configuration.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall / ICLR format:** Pages follow a standard ICLR single-column style with consistent margins, headers, section numbering, and readable body text. Visually easy to inspect as a conference paper.

- **Tables:** No tables are visible in the provided pages.

- **Figures generally:** Figures are visually clean and connected to the surrounding text, but many contain multiple small subplots with tiny legends, axis labels, tick labels, and dense shaded confidence bands. They are readable at page scale only with some effort.

- **Captions:** Captions are generally informative and specific, explaining what curves/settings are shown and often summarizing the takeaway. They are well connected to the visual content.

- **Page 1:** Title/authors/abstract are well formatted and readable. The author/email block is dense but acceptable. No figure/table issues.

- **Page 2:** Text-heavy page, but layout is clean. Bullet list is readable; colored section references stand out clearly.

- **Page 3:** No figures yet; typography and section headings are clear. Some dense paragraphs, but no major formatting issues.

- **Page 4:**  
  - **Figure 1** is informative, but the three training-curve panels have small legends and axis labels; line colors/shadings could be hard to distinguish when printed or viewed small.  
  - **Figure 2** is squeezed into the right column area; labels are small but mostly legible. Caption is clear.  
  - Layout is somewhat crowded around Figure 2, with text wrapping tightly around the visual.

- **Page 5:**  
  - Equation (1) is cleanly displayed and readable.  
  - **Figure 3** contains four subplots; titles and axes are small but still interpretable. Caption clearly explains the message.  
  - **Figure 4** is small, especially legends and tick labels; the two-panel layout is understandable but visually compressed.

- **Page 6:**  
  - **Figure 5** is reasonably sized, but legend entries and shaded regions are visually dense.  
  - **Figure 6** has three small panels; labels and legends are somewhat tiny. Caption is helpful and explains the dashed vertical line.  
  - Page has a crowded mid-page float/text arrangement but remains readable.

- **Page 7:**  
  - **Figure 7** is legible overall, though legends and tick labels are small.  
  - **Figure 8** is placed beside text and appears relatively small; caption is concise and connected.  
  - Dense paragraphing around figures makes the page visually busy.

- **Page 8:**  
  - The boxed “Adaptive Replay Ratio” callout is visually clear and helps inspection.  
  - **Figure 9** has six subplots; overall comparison is understandable, but individual legends/axes are small.  
  - **Figure 10** has multiple small panels and a long caption; detailed inspection requires zooming.  
  - Footnote/code link at bottom is readable but close to the lower page boundary.

- **Color/contrast:** The use of orange/blue/gray/red is mostly clear, but several plots rely heavily on color and light shaded confidence intervals; accessibility and grayscale print readability may be weaker.

- **Main presentation concern:** The paper is visually polished, but many figures pack several curves/subplots into limited space. Enlarging legends/axis labels or moving some detailed plots to larger appendix figures would improve readability.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

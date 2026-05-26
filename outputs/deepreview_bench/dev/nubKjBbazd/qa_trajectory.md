# Q&A Trajectory

## Contribution

### Q1

**Question:** How novel is APD relative to prior transfer-attack methods that use input transformations, masking/dropout/cutout, attention/CAM guidance, or gradient averaging? Are there closely related attacks that already drop image or perturbation regions during optimization, and if so, what is the meaningful technical difference?

**Answer:** APD appears only moderately novel: its main contribution is not the general recipe of stochastic transformations, masking/dropout, attention guidance, or gradient averaging, all of which are established ingredients in transferable attacks. The meaningful technical distinction is narrower: APD drops regions of the current perturbation by replacing those adversarial regions with the corresponding clean-image pixels, chooses drop centers from Grad-CAM++ attention peaks, uses multiple square scales around those centers, and averages gradients over these perturbation-dropped variants before the iterative update. This differs from ordinary cutout/random-erasing style transformations, which mask or zero image regions, and from DIM/TIM/SIM-style methods, which average gradients over resized, translated, or scaled inputs. It also differs from CAM/attention-guided attacks that use attention to weight or target salient features rather than explicitly removing perturbation regions to reduce inter-region perturbation synergy. However, because APD is essentially an EOT/gradient-averaging attack over a structured family of masked adversarial examples, and because the paper itself compares to a cutout variant, the novelty is incremental rather than foundational. Closely related methods already use transformations, random masking/cutout-like augmentation, attention maps, and gradient averaging; APD’s defensible novelty is the specific perturbation-level dropout operator with clean-image replacement, CAM-centered multi-scale mask selection, and the interpretation that this reduces dependence among perturbation regions.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper positions APD as a transferability enhancer that can be integrated with existing iterative attacks such as MI-FGSM, DIM, TIM, SIM, AAM, and AA-TI-DIM, indicating that the work builds on a mature family of transformation- and gradient-averaging-based attacks rather than introducing a wholly new attack paradigm.
- paper: In the method, APD uses Grad-CAM++ at each iteration to identify local maxima as drop-region centers; for each center it creates multiple dropped images with square regions of increasing side length, replaces the perturbation in those regions with the corresponding clean-image content, averages the gradients over the dropped images, and applies an I-FGSM-style update.
- paper: The appendix includes a comparison to a cutout-style variant that fills dropped regions with zeros, and APD reportedly performs better. This shows the authors recognize cutout/masking as a close baseline; the claimed difference is clean-image perturbation dropout rather than zero-mask image cutout.
- paper: The related-work summary discusses established transfer attacks including input diversity, momentum, translation-invariant attacks, scale-invariant attacks, intermediate-level attacks, reverse adversarial perturbation, and ghost networks. Thus several components adjacent to APD—input transformations, gradient aggregation, and transferability-oriented optimization—are not new.
- inference: APD can be interpreted as expectation-over-transformation or ensemble-gradient optimization over masked versions of the current adversarial example. That makes its conceptual novelty limited, but the exact mask construction—CAM-centered, multi-scale, perturbation-only dropout with clean-pixel replacement—is a meaningful implementation-level distinction from standard random input transformations or zero-valued cutout.
- retrieval: No external scholar retrieval results were available in this QA context, so the novelty judgment is based on the paper’s own positioning plus reviewer knowledge of common transfer-attack families. This lowers confidence about whether an uncited prior method performs almost the same perturbation-region dropout.

## Soundness

### Q1

**Question:** Does the paper adequately control for APD's increased computational cost and gradient evaluations when comparing to baselines—for example, by matching total gradient calls or wall-clock budget across attacks—and are any statistical uncertainty measures or repeated trials reported for the ASR improvements?

**Answer:** No. The paper only partially addresses APD's extra computation. The method itself averages gradients over multiple dropped images per iteration: with the reported default of up to 3 CAM centers and m=5 scales, APD can require about 15 gradient evaluations per attack iteration, in addition to CAM computation, while the main baselines are compared under the same iteration count T=10. The appendix acknowledges that APD has additional computational cost and includes a limited “same-computation” comparison where MI-FGSM with 15x more iterations is compared against APD-MI. However, this does not amount to a comprehensive control across all evaluated attacks, all APD variants, or actual wall-clock budgets. The main ASR improvements in Tables 1–3 therefore appear to be primarily fixed-iteration comparisons, not fully compute-matched comparisons. I also found no indication, from the described experimental sections, that the paper reports confidence intervals, standard deviations, statistical tests, or repeated-trial variability for the ASR gains; results are reported as single ASR percentages on a 1000-image ImageNet subset.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The method description states that APD creates multiple dropped versions of the adversarial image and averages gradients over n times m dropped images; the implementation uses up to 3 CAM centers and default m=5, implying many more gradient evaluations than a standard iterative attack at the same number of iterations.
- paper: The experimental setup uses default T=10 iterations and compares APD-integrated attacks against MI-FGSM, DIM, TIM, SIM, AAM, and AA-TI-DIM using ASR as the primary metric.
- paper: The appendix explicitly notes APD's additional computational cost and provides a limited same-computation discussion/Table 4 comparing APD-MI against MI-FGSM with 15 times more iterations, but this appears limited to MI-FGSM/APD-MI rather than the full set of baselines or wall-clock-matched evaluations.
- paper: The reported ASR improvements are given as single percentages or averages over model targets; the paper summary does not indicate reported standard deviations, confidence intervals, statistical significance tests, or repeated random trials.
- inference: Because APD changes the per-iteration computational budget, fixed-iteration ASR comparisons can overstate algorithmic gains relative to compute-matched baselines. The limited appendix check mitigates this concern somewhat but does not fully control for gradient-call or wall-clock budgets across the main experimental claims.

### Q2

**Question:** Are the attack baselines used in the paper sufficiently strong and current for a 2024 transferability paper, and do the ablations isolate the claimed contributions of APD—especially the CAM-guided region selection and perturbation-dropout mechanism—from simpler alternatives such as random masking, cutout/input dropout, or generic ensemble/augmentation-based gradient averaging?

**Answer:** The baselines are reasonably broad but not fully sufficient for a 2024 transferability paper, and the ablations only partially isolate APD’s claimed mechanisms. The paper compares APD against and on top of MI-FGSM, DIM, TIM, SIM, AAM, and AA-TI-DIM, and evaluates on normally trained models, adversarially trained models, defense/purification models, and diverse architectures including ViT-B/16. This is a meaningful baseline set. However, many of these are older canonical transfer attacks, and the evidence provided does not show comparison to a broader set of recent strong transfer methods or feature/gradient-stabilization attacks that were commonly relevant by 2023–2024. Thus, the baseline suite is not clearly state-of-the-art-current.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The experimental setup lists attack baselines including MI-FGSM, DIM, TIM, SIM, AAM, and AA-TI-DIM, with ImageNet evaluation on 1000 images and target models including Inc-v3, Inc-v4, IncRes-v2, Res-101, and adversarially trained Inc-v3_ens3, Inc-v3_ens4, and IncRes-v2_ens.
- paper: The paper reports that APD improves these baselines in single-source and ensemble-source settings, including improvements over MI, DIM, TIM, SIM, AAM, and AA-TI-DIM, and also tests defense models such as ResNeXt_DA, Res152_D, NRP, and NRP_resG plus diverse architectures including Seq2d_l, ViT-B/16, and MnasNet.
- paper: The ablations include CAM-based region selection versus random region selection, beta/scale and number-of-centers studies, a cutout-style comparison where dropped regions are filled with zeros, and a same-computation comparison against MI-FGSM with more iterations.
- inference: These ablations support that CAM-guided selection is better than the paper’s random-region variant and that replacing dropped regions with clean-image pixels is better than a zero-fill cutout variant. However, they do not fully rule out simpler explanations: APD averages gradients over many masked/dropout-transformed inputs, so gains may come from generic stochastic augmentation or ensemble-style gradient smoothing rather than the proposed perturbation-independence mechanism.
- inference: The same-computation comparison against longer MI-FGSM is helpful but too narrow: it does not compare against equally budgeted random masking, input dropout/cutout, stochastic transformation averaging, or generic multi-view gradient averaging across the stronger baselines. The paper also reports ASR values without clear statistical uncertainty, which limits confidence in small gains such as the defense-model improvements.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall (pp. 1–8):** The paper is broadly easy to visually inspect as an ICLR-style submission: consistent margins, header, page numbers, sectioning, and readable main text. The layout is dense but conventional.

- **Page 1:** Title/abstract layout is clean and readable. Title uses very wide small-caps/letter spacing, which looks somewhat heavy but not problematic.

- **Page 2, Figure 1:**  
  - Subfigure (a) image content is mostly understandable, but labels inside the image are small.  
  - Subfigure (b) bar charts are **hard to read**: axes, tick labels, model names, and legend text are very small.  
  - Caption is informative and clearly connects to panels 1(a) and 1(b), but it is very long and visually dense.

- **Page 5, Figure 2:** Images and model labels are legible; CAM overlays are visually clear. Caption is informative and directly describes the visual content. No major issue, though a color scale/legend is absent if exact heatmap meaning matters.

- **Page 5, Figure 3:** The figure is understandable, but region labels inside the right image are small. The figure is placed beside wrapped text, creating a narrow text column and a somewhat crowded visual block. Caption is concise and connected to the figure.

- **Page 7, Table 1:** The table is dense and compressed into four stacked subtables. Values are mostly legible at page scale but require effort; bolding many entries creates visual clutter. Caption is informative and explains bold values and the white-box marker.

- **Page 8, Tables 2–3:** Tables are more legible than Table 1. Captions are informative and connected to the content. Table 3 is especially easy to inspect.

- **Equations/notation (pp. 4, 6):** Equations are centered and generally legible. Some long mathematical expressions are visually dense but do not overflow. Equation numbering appears consistent where used.

- **Typography/formatting issues:** There are several spacing/formatting inconsistencies in text/citations, e.g., missing spaces around citations or parentheses such as “(FGSM)Goodfellow,” “PGD)Madry,” “1).Selective,” and “synergy(i.e.” These affect polish and readability.

- **Captions:** Generally informative and well connected to figures/tables. Main issue is that Figure 1 and Figure 2 captions are long paragraphs, making quick visual scanning harder.

- **Visual inspection as ICLR submission:** Acceptable overall, but the paper would be easier to review visually if small chart/table text were enlarged, long captions shortened or structured, and spacing/citation typography cleaned up.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

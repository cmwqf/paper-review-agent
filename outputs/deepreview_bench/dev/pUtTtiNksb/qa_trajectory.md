# Q&A Trajectory

## Contribution

### Q1

**Question:** Using external scholarly retrieval, how novel is FFCA-Net's main idea of coarse-to-fine stereo feature alignment for distributed/asymmetric stereo image compression relative to prior methods such as LDMIC, MSFDPM, DSIC/HESIC/SASIC/BCSIC, and related stereo matching or feature-warping compression works? Please identify whether the paper's components appear substantially new or mostly recombinations/adaptations.

**Answer:** FFCA-Net's contribution appears moderately novel but not fundamentally new: the main idea is best characterized as a targeted recombination and stereo-specific adaptation of existing components rather than a substantially new compression paradigm. The paper's own related-work discussion already identifies close antecedents: DSIC uses feature-domain disparity estimation and aligned auxiliary context through skip modules; HESIC uses homography-based alignment; SASIC learns inter-view shifts; BCSIC uses bidirectional contextual transforms; LDMIC uses cross-attention for global inter-view correlation; and MSFDPM performs multi-scale feature-domain patch matching for distributed image compression. Against that background, FFCA-Net's distinctive contribution is to combine these known ingredients into a faster decoder-side cascade: stereo-constrained patch matching along epipolar/disparity directions, reuse of matching across scales, hourglass-style sparse disparity refinement, channel-selective warping, and lightweight feature fusion. These design choices are plausible and useful, especially for lowering decoding latency, but the conceptual novelty is incremental: stereo/epipolar search constraints, coarse-to-fine matching, cost-volume/disparity refinement, warping, and lightweight fusion are all well-established ideas in stereo matching, optical flow, and learned stereo compression. The strongest contribution is therefore engineering integration for asymmetric/distributed stereo image compression, not invention of a new alignment principle. This matters for the Contribution dimension because the paper can still be valuable if the adaptation yields strong RD-speed tradeoffs, but the novelty claim should be framed as an efficient stereo-prior-aware system design rather than a substantially new methodological idea.

**Impact:** weakness, C2, confidence=medium

**Evidence:**
- paper: The paper states that prior stereo compression methods already use alignment or inter-view modeling: DSIC estimates disparity in the feature domain and incorporates aligned auxiliary context through skip modules; HESIC uses a deep homography estimator; SASIC learns element-wise shifts; and BCSIC uses bidirectional contextual transformation modules and conditional entropy models.
- paper: The paper also states that learned distributed methods include LDMIC, which uses cross-attention to capture global correlations across viewpoints, NDIC, which extracts side-information features but lacks registration, and MSFDPM, which performs patch matching in the multi-scale feature domain.
- paper: FFCA-Net's own method consists of stereo patch matching constrained to same-row/disparity-direction windows, grouped-convolution correlation computation, reuse of high-resolution matching across scales, hourglass-based sparse stereo refinement with cost volumes, sparse channel warping based on feature differences, and Fast Feature Fusion using lightweight convolutional blocks.
- retrieval: External scholarly retrieval for direct pre-2024 matches to "FFCA-Net", "coarse-to-fine alignment", "LDMIC", "MSFDPM", "DSIC", "HESIC", "SASIC", "BCSIC", and feature-warping stereo compression returned no additional direct prior paper records beyond the paper's cited baseline descriptions. A later Semantic Scholar result, DIC-DDA 2026, is post-submission and not prior art, but it confirms that asymmetric distributed image compression continues to focus on alignment between decoded target features and side information.
- inference: Because most FFCA-Net components map onto known families of stereo matching, feature warping, patch matching, attention/alignment, cost-volume disparity estimation, sparse refinement, and lightweight fusion, the contribution is mainly their efficient combination under stereo-prior constraints for decoder-side distributed compression. The novelty is therefore meaningful but incremental.

**Retrieved Papers:**
- DIC-DDA: Learned Asymmetric Distributed Image Compression via Dual Domain Alignment | 2026 | https://www.semanticscholar.org/paper/d2b2a7fe04ba4b9fdd746fdb2372cc2443fcacd3 | Low as prior-art evidence because it postdates the FFCA-Net submission; useful only as contextual retrieval showing that later asymmetric distributed image compression work also centers on side-information alignment and refinement.

### Q2

**Question:** Using external scholarly retrieval where useful, how strong and broadly meaningful are FFCA-Net's empirical contributions relative to the closest prior stereo/distributed image compression methods? In particular, do the reported rate-distortion and decoding-speed gains appear to establish a state-of-the-art advance across standard datasets, or are they limited by dataset choice, evaluation protocol, missing baselines, or implementation comparability?

**Answer:** FFCA-Net's empirical contribution is fairly strong and meaningful, but it should be framed as a qualified state-of-the-art advance rather than an unequivocal one. On the paper's chosen benchmarks, FFCA reports very competitive rate-distortion results against relevant stereo and distributed compression baselines, especially on MS-SSIM: it is best on all three datasets by MS-SSIM BD-rate and achieves large savings versus BPG. It also reports the lowest decoding latency and FLOPs among the compared methods on InStereo2K, suggesting a real contribution on the speed-quality tradeoff. However, the SOTA claim is limited by several factors: PSNR superiority is not uniform, with LDMIC better than FFCA on Cityscapes and InStereo2K PSNR BD-rate; some baselines are not run on all datasets; HESIC and BCSIC results are taken from prior papers rather than uniformly re-evaluated; LDMIC is evaluated without its fine-tuning strategy; and decoding-speed comparison is reported only for InStereo2K at one resolution and may depend on implementation/hardware comparability. Thus, the experiments support FFCA as a strong contribution in learned distributed stereo compression, especially for MS-SSIM and decoding speed, but the evidence is not broad or standardized enough to conclusively establish across-the-board SOTA over all closest prior methods.

**Impact:** strength, C2, confidence=high

**Evidence:**
- paper: The paper compares against BPG, Cheng2020, HESIC, DSIC, SASIC, BCSIC, NDIC, MSFDPM, LDMIC-fast, and LDMIC on KITTI-stereo, Cityscapes, and InStereo2K. Table 1 reports FFCA BD-rate versus BPG of KITTI -74.62% PSNR and -85.18% MS-SSIM, Cityscapes -37.84% PSNR and -55.36% MS-SSIM, and InStereo2K -47.02% PSNR and -69.75% MS-SSIM. The text states that FFCA's MS-SSIM-based BD-rate outperforms other methods across all datasets.
- paper: The same table shows that FFCA is not best under PSNR on every dataset: LDMIC reports -38.09% PSNR on Cityscapes versus FFCA -37.84%, and -58.45% PSNR on InStereo2K versus FFCA -47.02%. The setup also notes that HESIC and BCSIC were not validated on Cityscapes, that their results were taken from the original papers, and that LDMIC was evaluated without the fine-tuning strategy from Zhang et al.
- paper: For computational complexity, Table 2 reports FFCA at 781.76G FLOPs and 4.91s decoding time on InStereo2K at 832 x 1024, compared with DSIC 15.03s, HESIC 28.56s, SASIC 19.58s, NDIC 5.64s, MSFDPM 23.85s, LDMIC-fast 6.66s, and LDMIC 27.77s. The paper claims 3.06-5.82x faster decoding than joint methods and 1.15-4.91x faster than asymmetric DSC methods.
- retrieval: No external scholarly retrieval results were provided for this query, so no additional external papers are used as evidence beyond the paper map and provided paper text observations.
- inference: For the Contribution dimension, the empirical case is important because it shows FFCA is not just a new architecture but improves the measured rate-distortion and runtime tradeoff over many relevant baselines. The contribution is nevertheless somewhat narrowed by nonuniform PSNR wins, incomplete dataset coverage for some baselines, and partial implementation comparability.

### Q3

**Question:** Assess the likely broader impact and scope of FFCA-Net's contribution: is the method mainly an engineering improvement for a narrow stereo-image compression setting, or does it introduce ideas likely to transfer to broader learned compression or multi-view coding tasks? Please consider practical assumptions such as rectified stereo geometry, decoder-side side information, computational cost, and applicability beyond the tested datasets.

**Answer:** FFCA-Net appears to be a strong engineering contribution for a fairly specific learned distributed stereo-image compression setting, rather than a broadly general compression idea. Its main novelty is an efficient cascade of stereo-prior-based feature alignment, sparse refinement, and lightweight fusion at the decoder. These ideas could transfer to some nearby multi-view or stereo coding tasks, especially where views are rectified, synchronized, calibrated, and one view is available as decoder-side side information. However, the method relies heavily on stereo-specific assumptions: patch matching is constrained to the same row and disparity direction, the architecture assumes decoder-side side information, and the evaluation is limited to three stereo datasets. The paper itself acknowledges that more general priors are needed to broaden applicability. Therefore, for the Contribution dimension, I would treat FFCA-Net as an important but scoped contribution: practically useful and well targeted, but not clearly a general advance for learned compression beyond rectified stereo or closely related multi-view settings.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: The method's stereo patch matching explicitly narrows the search to windows in the same row and within the disparity direction, using stereo-image priors. This supports efficiency but also indicates dependence on rectified stereo geometry.
- paper: The architecture is framed as distributed stereo image compression, where correlated views are independently encoded and side information is exploited at the decoder through coarse-to-fine feature alignment.
- paper: Experiments cover KITTI-stereo, Cityscapes, and InStereo2K, with strong BD-rate gains and faster decoding; Table 2 reports 781.76G FLOPs and 4.91s decoding time at 832 x 1024 on InStereo2K, so the method is faster than baselines but still computationally substantial.
- paper: The conclusion states that future work should extract more general priors to broaden applicability to various scenarios and explore more efficient ways to apply these priors for faster encoding and decoding.
- retrieval: The retrieved related work, including Neural Distributed Image Compression with Cross-Attention Feature Alignment, shows that decoder-side side information and feature alignment for stereo pairs are already an active line of work; FFCA-Net's contribution is therefore best understood as a more stereo-prior-aware and efficient variant within that line.
- inference: Because FFCA-Net's gains come from exploiting rectified stereo constraints, sparse disparity refinement, and lightweight fusion, the contribution is likely transferable to calibrated stereo or nearby multi-view settings, but less clearly to arbitrary learned image compression, unrectified cameras, wide-baseline scenes, video, or general multi-view coding without similar geometry and side-information assumptions.

**Retrieved Papers:**
- FFCA-Net: Stereo Image Compression via Fast Cascade Alignment of Side Information | 2023 | https://www.semanticscholar.org/paper/c20c1e5d22dae47037344a6523b6a1ccf433c9a1 | Primary paper; directly supports claims about fast cascade alignment, stereo priors, decoder-side side information, and reported speedups.
- Neural Distributed Image Compression with Cross-Attention Feature Alignment | 2022 | https://www.semanticscholar.org/paper/50c34794f6cc8e85150e9e41fedbb967d2ffbb50 | Relevant prior work on learned distributed compression with decoder-side side information and feature alignment for stereo image pairs, indicating FFCA-Net builds within an existing problem setting.
- DIC-DDA: Learned Asymmetric Distributed Image Compression via Dual Domain Alignment | 2026 | https://www.semanticscholar.org/paper/d2b2a7fe04ba4b9fdd746fdb2372cc2443fcacd3 | Related asymmetric distributed image compression work emphasizing alignment between target image and side information; useful context for the broader family of decoder-side alignment methods.

## Soundness

### Q1

**Question:** Are the comparisons to the listed baselines methodologically fair: were baseline models retrained or evaluated under the same datasets, resolutions, bitrates, and hardware/software settings, especially for decoding latency and FLOPs?

**Answer:** The comparisons are only partially fair. The paper does make a reasonable effort to evaluate many baselines under common conditions: it reports the same three datasets, common RD metrics, and says that all baselines except HESIC and BCSIC were re-evaluated using open-source code and published parameters. It also reports a common complexity setting for Table 2: InStereo2K at 832×1024 resolution, and gives the experimental hardware as two Intel Xeon Silver 4210 CPUs and two NVIDIA 2080Ti GPUs. However, the methodology is not fully controlled. HESIC and BCSIC results are taken from their original papers rather than re-run, and they are not validated on Cityscapes. The paper says baselines were re-evaluated with published parameters, not retrained or fine-tuned on the same splits; for LDMIC it explicitly disables the fine-tuning strategy from the original paper. For latency/FLOPs, the paper lists numbers but does not specify enough implementation details to ensure strict fairness, such as batch size, CPU vs GPU timing protocol, warm-up, precision, software versions, whether all baseline implementations were equally optimized, or whether timing includes entropy decoding/I/O. Therefore, the RD comparisons against re-evaluated open-source baselines are moderately credible, but the baseline comparison is methodologically weaker for copied-paper baselines and especially for decoding latency/FLOPs claims.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: The paper states that baselines include BPG, Cheng2020, HESIC, SASIC, BCSIC, DSIC, NDIC, MSFDPM, LDMIC-fast, and LDMIC, and that “for HESIC and BCSIC, we used the results reported in their respective papers” while “excluding HESIC and BCSIC, we re-evaluated the rest of the baseline models utilizing their open-source codes and published parameters.”
- paper: The paper further notes that HESIC and BCSIC “have not been validated on the Cityscapes dataset,” which means not all baselines are evaluated on all datasets under the same conditions.
- paper: For LDMIC, the authors state that “to ensure a fair comparison, we abstained from the fine-tuning strategy mentioned in Zhang et al. (2023),” indicating that at least one baseline is intentionally evaluated without its original fine-tuning procedure rather than retraining all models uniformly.
- paper: The implementation section reports experiments on “two Intel(R) Xeon(R) Silver 4210 CPUs and two NVIDIA 2080ti GPUs,” and Table 2 states that computational complexity is tested on InStereo2K at “832 × 1024” resolution.
- paper: Table 2 reports FLOPs and decoding time for DSIC, HESIC, SASIC, NDIC, MSFDPM, LDMIC-fast, and FFCA, and claims FFCA has the lowest FLOPs and latency, but the surrounding text does not provide a full timing protocol or software/runtime controls.
- inference: Using published numbers for some baselines and re-evaluated published parameters for others creates a risk of unequal dataset preprocessing, model checkpoints, optimization, and runtime measurement. This is particularly consequential for latency/FLOPs, where hardware, codebase, precision, and measurement protocol can strongly affect reported speedups.

### Q2

**Question:** Do the ablation studies adequately isolate each claimed component's contribution to both rate-distortion performance and decoding speed, including whether “W/O FFF” and the acceleration ablations preserve comparable model capacity and quality?

**Answer:** No. The ablations provide useful but incomplete support. For rate-distortion, Table 3 shows that removing HSSR hurts performance and removing both SPM and HSSR hurts much more, but the SPM contribution is not cleanly isolated because SPM is only evaluated jointly with removing HSSR. For FFF, the rate-distortion comparison is especially weak: “W/O FFF” has nearly identical quality to the proposed model and even slightly better BD-rate (-54.71% vs. -54.51%), while the paper explains FFF mainly as a decoding-speed component. However, the main ablation table does not report integrated decoding latency for “W/O FFF.” The appendix gives component-level acceleration comparisons, but these compare lightweight proposed modules against heavier alternatives with different parameter counts, e.g. FFF has 3.04M parameters versus 7.02M for baseline Feature Fusion, and HSSR has 0.24M versus 8.64M for Parametric Skip Function. Thus the acceleration experiments do not clearly preserve comparable capacity or matched reconstruction quality. This matters for Soundness because the paper’s claims that each component separately improves rate-distortion and/or speed are not fully causally isolated; some conclusions rely on entangled ablations and unmatched speed baselines.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: Section 4.3 says the ablations are on InStereo2K and Table 3 reports BD-rate and BD-PSNR: W/O SPM HSSR = -16.61%, 0.52dB; W/O HSSR = -49.31%, 2.04dB; W/O FFF = -54.71%, 2.25dB; Proposed = -54.51%, 2.27dB.
- paper: The paper text states that W/O HSSR removes the fine-grained refinement module, while W/O SPM & HSSR removes both coarse and fine-grained alignment, so SPM is not independently ablated from HSSR.
- paper: For FFF, the paper states that Fast Feature Fusion is primarily designed to accelerate decoding and that the lightweight decoder can slightly outperform the more complex decoder at lower bit rates, with a minor decline at higher bit rates.
- paper: The appendix acceleration ablations report component-level speed and parameter comparisons: Stereo PM 0.76s CPU / 0.027s GPU versus Multi-scale PM 15.32s / 0.46s; FFF 1.84s CPU and 3.04M parameters versus Feature Fusion 2.20s and 7.02M parameters; HSSR 1.41s CPU and 0.24M parameters versus Parametric Skip Function 4.22s and 8.64M parameters.
- retrieval: No external retrieved papers were provided for this question.
- inference: Because the acceleration baselines have substantially different parameter counts and are reported mostly as component-level speed comparisons rather than matched end-to-end rate-distortion-speed comparisons, they do not fully isolate whether speed gains come from the claimed design rather than reduced capacity or altered quality.

### Q3

**Question:** Are the training/evaluation protocol and statistical reporting sufficient to support the rate-distortion superiority claims, including dataset splits, number of test images, bitrate operating points, BD-rate computation details, confidence intervals or variance across runs?

**Answer:** No. The protocol is partially specified but not sufficient to fully support the rate-distortion superiority claims. The paper does provide dataset splits and test-set sizes in the appendix, and it lists the lambda values used to generate multiple bitrate operating points. It also reports PSNR, MS-SSIM, BD-rate, BD-PSNR, and RD curves across KITTI-stereo, Cityscapes, and InStereo2K. However, the statistical reporting is weak: there are no confidence intervals, no variance across random seeds or training runs, no per-image dispersion, and no significance testing. The BD-rate/BD-PSNR computation is also under-described and even appears conceptually misstated in the metrics description, where BD-PSNR is described as evaluating bitrate savings and BD-rate as determining PSNR gains, which is the reverse of the usual interpretation. Because the main empirical claim is rate-distortion superiority, especially via BD-rate comparisons, these omissions reduce confidence that the reported gains are robust rather than dependent on implementation choices, curve fitting details, or run-to-run variation.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: Appendix 6.1.1 gives explicit dataset splits and test sizes: Cityscapes has 2975 train, 500 validation, and 1525 test pairs; KITTI-stereo has 1578 training and 790 test pairs; InStereo2K has 2010 training and 50 test pairs.
- paper: Appendix 6.1.2 lists bitrate operating points through lambda values: seven lambda values for InStereo2K and six for KITTI and Cityscapes, along with epochs, batch size, crop sizes, and padding details.
- paper: Section 4.1 states that bpp, PSNR, MS-SSIM, BD-PSNR, and BD-rate are used, and Section 4.2 reports BD-rate results and RD curves. However, the metrics text says BD-PSNR evaluates bitrate savings and BD-rate determines PSNR gains, which is inconsistent with standard BD metric definitions.
- paper: The experimental setup says some baselines were re-evaluated with open-source code and published parameters, while HESIC and BCSIC used results reported in their respective papers; no confidence intervals, repeated-run statistics, seeds, or variance estimates are reported in the provided paper map or observations.
- retrieval: No retrieved papers were provided, so no external retrieval evidence is used.
- inference: For a strong Soundness case on rate-distortion superiority, dataset splits and operating points are necessary but not enough; BD-rate computation details and uncertainty estimates are important because small or method-dependent RD curve differences can be affected by interpolation, bitrate range, model training randomness, and baseline evaluation differences.

### Q4

**Question:** Does the paper clearly justify the distributed stereo compression formulation and bitrate accounting: specifically, is the side-information image assumed to be already available at the decoder, are any costs for transmitting side information/alignment metadata included, and are these assumptions applied consistently across joint stereo, asymmetric/distributed, and single-image baselines?

**Answer:** No. The paper motivates FFCA-Net with distributed source coding and repeatedly states that side information is used at the decoder, which implies that the auxiliary/side image or its features are assumed to be available there. However, the formulation does not clearly state the operational source of that side information, whether the auxiliary view must itself be transmitted, or whether its transmission cost is excluded by assumption. The rate-distortion loss includes only the compression rate of the latent representation R(z), and the experimental metric defines bpp generically without specifying whether it counts only the main-view bitstream or also any auxiliary-view, side-information, feature-extraction, patch-matching, disparity, or alignment metadata costs. The method computes patch correspondences and disparity-like refinement at the decoder, but the paper does not describe any transmitted alignment metadata, suggesting these are decoder-computed and uncounted; this is plausible, but not explicitly accounted for. As a result, the bitrate comparison across single-image baselines, joint stereo codecs, and asymmetric/distributed baselines is under-specified. This matters for Soundness because the core compression gains depend on fair and consistent rate accounting; if FFCA excludes the cost of obtaining the side-information view while joint or single-image methods are evaluated under different assumptions, the reported BD-rate improvements may not correspond to a comparable compression problem.

**Impact:** weakness, C3, confidence=high

**Evidence:**
- paper: The introduction cites distributed source coding and says correlated sources are independently encoded while side information is utilized at the decoder; FFCA is proposed to incorporate side information at the decoder.
- paper: The methodology says the main-view image is passed through a baseline single-image encoder-decoder, while a feature extraction network extracts multi-scale side-information features; it also refers to “lossless side information.”
- paper: The training loss is defined as L = R(z) + lambda((1-alpha)d1 + alpha d2), where R denotes the compression rate of the latent representation z; no side-information rate or alignment-metadata rate is included in this expression.
- paper: The experiments define bpp as the bitrate and compare single-image, joint stereo, and distributed compression baselines, but the provided setup does not specify whether bpp is measured per main image, per stereo pair, or with side-information costs included.
- retrieval: No retrieved external papers were provided for this question; the assessment is based on the paper map and quoted paper observations only.
- inference: Because the side-image availability and rate accounting are not explicitly specified, the most reasonable reviewer judgment is that the paper assumes decoder-side side information is available or separately obtained, but fails to justify and consistently account for that assumption across baselines.

## Presentation

### Q1

**Question:** Inspect the PDF pages for presentation evidence: readability, figures, tables, captions, layout, and formatting.

**Answer:** VLM page observations:
- **Overall ICLR visual format:** Mostly follows the ICLR single-column style with readable body text, headers, page numbers, and adequate margins. Visually inspectable, but several figures are too small and there are obvious formatting/markup issues.

- **Pages 1–2:** Text-only pages are readable and conventionally formatted. Introduction/related work is dense but visually clean. No figure/table issues.

- **Page 3, Figure 1:** The caption is informative and clearly tied to subpanels (a)–(c). The high-level diagram is understandable, but some internal labels/icons and image thumbnails are small and hard to inspect without zooming.

- **Page 4, Figure 2:** Main architecture figure is useful and connected to the caption, but many labels/arrows inside the diagram are small. The entire caption is colored red, which looks like unremoved revision markup and is inconsistent with the rest of the paper.

- **Page 5, Figures 3–4:** Both figures are somewhat cramped. Figure 3’s colored arrows/insets are hard to read at page scale; Figure 4’s block labels are very small. Captions are minimal and could better explain what the reader should notice.

- **Pages 4–6, equations:** Equations are generally readable and numbered consistently. Some notation is visually dense, but alignment and spacing are mostly acceptable.

- **Page 6:** Large blocks of red text appear in the main body and around equation (7), again suggesting unremoved markup or inconsistent formatting. This significantly hurts presentation polish. Section title has a typo: **“Loss Fuction”** should be **“Loss Function.”**

- **Page 7, Figure 5:** Six rate–distortion plots are well organized, but legends, tick labels, and method names are very small. The plots are only comfortably legible with zoom. Caption is clear but brief.

- **Page 8, Table 1:** Table is mostly legible and well structured. Caption has a typo/spacing issue: **“inred”** should be **“in red.”** Reliance on red/blue to indicate best/second-best may be problematic for grayscale printing or color-impaired readers.

- **Page 8, Figure 6:** Visual comparisons are informative, with zoomed regions, but thumbnails and overlaid PSNR/BPP labels are quite small. The caption is connected to the visual content, though it could specify datasets/examples more clearly.

- **Major presentation concerns:** Red revision-like text/captions, small figure labels/legends, a visible section-title typo, and several captions that are informative but too terse. These issues should be fixed before submission for a polished ICLR presentation.

**Impact:** neutral, C1, confidence=medium

**Evidence:**
- pdf_image:vlm_pages

### Q2

**Question:** Please inspect the paper text/PDF for writing quality, organization, and clarity of notation/terminology in the main method and experiments sections. Are the method components, equations, variables, and experimental comparisons easy to follow, or are there ambiguities/typos that affect reviewer understanding?

**Answer:** The paper is broadly organized in a reasonable way, with a standard Methodology section followed by experimental setup, quantitative results, visualization, and implementation details. The high-level flow of the method—stereo patch matching, sparse stereo refinement, and fast feature fusion—is understandable. However, the presentation has several clarity problems that materially slow reviewer understanding. In the method section, notation is sometimes inconsistent or ambiguous: the text initially appears to denote both primary and auxiliary features with similar symbols in the markdown extraction, while the PDF clarifies these as h_i for the reconstructed/main view and side view features; variables such as h_y, h_y*, h_y**, h_x-hat, disparity maps dp_i, and the channel index g are introduced quickly and not always consistently explained. Equation references are also awkward: the paper says mapping relationships are obtained “by 3” rather than “by Eq. 3,” and Eq. 5 uses scale factors like 2^{i-1} without much explanation of coordinate conventions. There are also visible typos in headings and prose, e.g. “MULTI-SALE FEATURE-DOMAIN” instead of “multi-scale,” “LOSS FUCTION,” missing spaces such as “simplicity,we,” and capitalization issues such as “we actively select” after a period. These are not merely cosmetic because the method relies on several nested feature transformations, and imprecise notation makes it harder to verify the algorithm.

**Impact:** weakness, C2, confidence=high

**Evidence:**
- paper: PDF pages 3–6 show that the method is organized into Section 3, Section 3.1 “Stereo Patch Matching,” Section 3.2 “Hourglass-Based Sparse Stereo Refinement,” and Section 3.3 loss, which gives the reader a useful component-level structure.
- paper: PDF page 4 contains the heading “STEREO PATCH MATCHING ON MULTI-SALE FEATURE-DOMAIN,” a typo in a central method subsection title. PDF page 6 contains the heading “LOSS FUCTION.”
- paper: PDF page 5 states that the method obtains mapping relationships “by 3 to obtain u1(m,n), v1(m,n),” which appears to mean Eq. 3 but is written unclearly. The same page introduces Eq. 5 for scaling mappings across layers without substantial explanation of coordinate scaling conventions.
- paper: PDF page 6 introduces the sparse channel set G and complement Gc, then defines warping in Eq. 8. The notation is compact but dense, and symbols h_y*, h_y**, dp_i, and channel-specific h_{.;g} require careful tracking across several paragraphs.
- paper: PDF page 7 experiment text defines datasets, metrics, baselines, and implementation details, which helps follow the experimental comparisons. However, the same page’s extracted PDF text for Figure 5 is garbled with many /uni000... tokens, indicating that the rate-distortion figure is difficult to inspect from text extraction and may have rendering/font accessibility issues.
- paper: PDF page 8 Table 1 presents BD-rate comparisons across dataset, metric, and method categories, but the table has formatting issues such as missing spacing before “FFCA(Proposed)” and “best results inred,” which detract from readability.
- inference: The main contribution is technically understandable at a high level, but the number of notation transitions and visible typos/formatting issues are significant enough that a reviewer must spend extra effort reconstructing the exact algorithmic meaning and checking experimental comparisons.

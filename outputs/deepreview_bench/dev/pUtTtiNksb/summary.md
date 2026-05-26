# Paper Map

```text
PAPER MAP
Title: FFCA-Net: Stereo Image Compression via Fast Cascade Alignment of Side Information
Authors: Anonymous authors
Venue: ICLR 2024
Submission date: 2023-12-28

SECTIONS
[s1] Introduction and Abstract
Summary: The paper addresses stereo image compression under a distributed source coding setting, where correlated views are encoded independently and side information is used at the decoder. It proposes FFCA-Net, a coarse-to-fine feature alignment framework intended to improve compression quality and reduce decoding latency. The section lists contributions including stereo patch matching, sparse stereo refinement, fast feature fusion, and experiments on three stereo datasets.
Key items:
- problem: Existing deep distributed stereo image compression methods are described as not fully exploiting stereo-image priors and having high decoding latency.
- motivation: Distributed Source Coding motivates independent encoding of correlated stereo views with joint decoding using side information.
- claim: FFCA-Net uses coarse-to-fine alignment of side information features at the decoder.
- claim: The abstract claims experimental superiority over traditional and learning-based SIC methods on InStereo2K, KITTI, and Cityscapes.
- result: The abstract claims 3 to 10-fold faster decoding speed than other methods.
- method_component: Main components are stereo patch matching, hourglass-based sparse stereo refinement, and Fast Feature Fusion.

[s2] Related Work
Summary: This section surveys learned single-image compression, stereo image compression, and learned distributed source coding. It contrasts joint encoding stereo methods with asymmetric distributed approaches that use decoder-side information. Figure 1 summarizes joint encoding, asymmetric DSC, and the proposed coarse-to-fine alignment structure.
Key items:
- baseline: Single-image compression references include BPG, Ballé-style learned compression, Minnen et al., Cheng et al., and He et al.
- baseline: Stereo compression baselines discussed include DSIC, HESIC, SASIC, and BCSIC.
- baseline: Distributed image compression baselines discussed include Ayzik and Avidan, NDIC, MSFDPM, and LDMIC.
- motivation: The paper states that prior distributed methods either lack effective registration or use complex patch matching or attention modules without fully exploiting stereo priors.
- other (Figure 1): Architectural categories for stereo coding are illustrated as joint encoding and asymmetric DSC.

[s3] Methodology
Summary: This section defines FFCA-Net as a cascaded coarse-to-fine alignment method operating on decoder features from a baseline single-image compressor and side-information features from a feature extraction network. It describes stereo patch matching, hourglass-based sparse stereo refinement, Fast Feature Fusion, and the rate-distortion training loss with feature distortion. Figure 2 gives the overall architecture.
Key items:
- method_component (Section 3.1): Stereo patch matching restricts feature-domain patch search to same-row and disparity-direction windows using stereo priors.
- method_component (Section 3.1): Grouped convolution is used to parallelize correlation computation for patch matching.
- method_component (Equation 5): Inter-patch correlations are computed only on the first high-resolution feature layer and reused with scale transformations for other layers.
- method_component (Section 3.2): Hourglass-based sparse stereo refinement builds concatenated cost volumes across scales and predicts disparity maps for fine-grained feature alignment.
- method_component (Equations 7-8): Sparse alignment warps only channels whose feature differences exceed threshold mu, leaving other channels unchanged.
- method_component (Equation 9): The loss combines latent bitrate, image reconstruction distortion, and feature-level inter-view distortion.

[s4] Experiments: Setup
Summary: This section describes the datasets, metrics, baselines, implementation, and training hyperparameters used to evaluate FFCA-Net. Experiments cover three high-resolution stereo datasets representing outdoor distant-view and indoor near-view scenes. The method is implemented in PyTorch and trained using Adam.
Key items:
- dataset (Section 4.1): Datasets are KITTI-stereo, Cityscapes, and InStereo2K.
- metric (Section 4.1): Metrics include bpp, PSNR, MS-SSIM, BD-PSNR, and BD-rate.
- baseline (Section 4.1): Single-image baselines are BPG and Cheng2020.
- baseline (Section 4.1): Joint stereo baselines are HESIC, SASIC, BCSIC, and DSIC.
- baseline (Section 4.1): Distributed compression baselines are NDIC, MSFDPM, LDMIC-fast, and LDMIC.
- other (Section 4.1): Reported hyperparameters include mu = 0.5, patch size B = 16, alpha = 0.1, and learning rate 1e-4.

[s5] Experiments: Results and Analysis
Summary: This section reports rate-distortion curves, BD-rate comparisons, visual examples, and computational complexity. FFCA is compared against traditional, joint stereo, and distributed compression baselines. The paper reports lower decoding FLOPs and latency than the listed baselines on InStereo2K at 832 x 1024 resolution.
Key items:
- result (Table 1): Table 1 reports FFCA BD-rate versus BPG as KITTI -74.62% PSNR and -85.18% MS-SSIM, Cityscapes -37.84% PSNR and -55.36% MS-SSIM, and InStereo2K -47.02% PSNR and -69.75% MS-SSIM.
- result (Figure 5): Figure 5 shows rate-distortion curves for PSNR and MS-SSIM across the compared methods.
- result (Section 4.2): The text states FFCA outperforms other methods by MS-SSIM-based BD-rate on all datasets.
- result (Figure 6): Visual comparisons report higher PSNR with fewer or equivalent bits than BPG and MSFDPM, while preserving structural details at low bit rates.
- result (Table 2): Table 2 reports FFCA with 781.76G FLOPs and 4.91s decoding time on InStereo2K at 832 x 1024 resolution.
- claim (Section 4.2): The paper states FFCA decoding latency is 3.06-5.82 times faster than joint decoding methods and 1.15-4.91 times faster than asymmetric DSC methods.

[s6] Ablation Study
Summary: This section studies the impact of hourglass-based sparse stereo refinement, stereo patch matching, and Fast Feature Fusion on InStereo2K. Ablations are reported with BD-rate and BD-PSNR. The appendix is referenced for decoding-speed ablations.
Key items:
- ablation (Table 3): W/O HSSR removes the fine-grained refinement module.
- result (Table 3): W/O HSSR reports BD-rate -49.31% and BD-PSNR 2.04dB.
- ablation (Table 3): W/O SPM HSSR removes both coarse and fine-grained alignment.
- result (Table 3): W/O SPM HSSR reports BD-rate -16.61% and BD-PSNR 0.52dB.
- ablation (Table 3): W/O FFF replaces or removes the fast feature fusion design used to accelerate decoding.
- result (Table 3): Proposed FFCA reports BD-rate -54.51% and BD-PSNR 2.27dB in the ablation table.

[s7] Conclusion
Summary: The conclusion restates FFCA-Net as a fast cascaded framework for distributed stereo image compression. It summarizes that coarse-to-fine feature matching aligns decoder side information with main-view information and reports encoding gains with lower decoding latency. It also states two future work directions related to priors and efficiency.
Key items:
- claim: FFCA-Net is described as effectively leveraging stereo view information through coarse-to-fine feature matching.
- result: The conclusion states FFCA achieves superior encoding gains while maintaining lower decoding latency than existing methods.
- stated_limitation: Future work can extract more general priors to broaden applicability to various scenarios.
- stated_limitation: Future work can explore more efficient ways to apply priors to accelerate encoding and decoding processes.

[s8] Appendix
Summary: The appendix provides dataset split details, training settings, crops, lambda values, padding strategy, and acceleration ablations for the three main model components. It compares stereo patch matching, Fast Feature Fusion, and hourglass-based sparse stereo refinement against component-level baselines.
Key items:
- dataset (Appendix 6.1.1): Cityscapes has 5000 image pairs with 2975 train, 500 validation, and 1525 test pairs at 2048 x 1024.
- dataset (Appendix 6.1.1): KITTI-stereo has 1578 training pairs and 790 test pairs at 1242 x 375.
- dataset (Appendix 6.1.1): InStereo2K has 2010 training pairs and 50 test pairs at 1080 x 860.
- result (Table 4): Stereo PM reports 0.76s CPU and 0.027s GPU inference, versus Multi-scale PM at 15.32s CPU and 0.46s GPU.
- result (Table 5): Fast Feature Fusion reports 1.84s CPU inference and 3.04M parameters, versus the baseline Feature Fusion at 2.20s and 7.02M parameters.
- result (Table 6): Hourglass-based sparse stereo refinement reports 1.41s CPU inference and 0.24M parameters, versus Parametric Skip Function at 4.22s and 8.64M parameters.

GLOBAL INDEX
Claims:
- [s1] FFCA-Net is proposed to leverage decoder-side stereo side information through fast cascade alignment.
- [s1] The paper claims higher-quality reconstructed images with lower bit consumption and faster decoding than state-of-the-art SIC methods.
- [s5] The paper states FFCA is faster in decoding than both joint decoding and asymmetric DSC baselines.
- [s7] The conclusion states FFCA achieves encoding gains while maintaining lower decoding latency.
Method components:
- [s3] Baseline single-image encoder-decoder produces multi-scale main-view decoder features.
- [s3] Feature extraction network extracts multi-scale side-information features.
- [s3] Stereo patch matching performs coarse feature-domain matching using same-row and disparity-direction constraints.
- [s3] Grouped convolution is used for parallel patch correlation computation.
- [s3] Hourglass-based sparse stereo refinement builds cost volumes and predicts disparity maps for fine alignment.
- [s3] Sparse channel selection warps only channels with large inter-view feature differences.
- [s3] Fast Feature Fusion uses shuffle blocks and depthwise separable convolutions to fuse aligned features.
- [s3] Training loss combines bitrate, reconstruction distortion, and feature-domain distortion.
Datasets:
- [s4] KITTI-stereo, described as outdoor distant-view stereo data.
- [s4] Cityscapes, described as outdoor distant-view stereo data.
- [s4] InStereo2K, described as indoor near-view stereo data.
- [s8] Appendix gives dataset sizes and train/test splits for Cityscapes, KITTI-stereo, and InStereo2K.
Baselines:
- [s4] BPG traditional single-image compression baseline.
- [s4] Cheng2020 learned single-image compression baseline.
- [s4] Joint stereo compression baselines: HESIC, SASIC, BCSIC, and DSIC.
- [s4] Distributed compression baselines: NDIC, MSFDPM, LDMIC-fast, and LDMIC.
- [s8] Component acceleration baselines include Multi-scale PM, Feature Fusion from Huang et al., and Parametric Skip Function from DSIC.
Ablations:
- [s6] W/O HSSR removes hourglass-based sparse stereo refinement.
- [s6] W/O SPM HSSR removes both stereo patch matching and hourglass-based sparse stereo refinement.
- [s6] W/O FFF evaluates the system without the proposed Fast Feature Fusion design.
- [s8] Appendix acceleration ablations compare each main component to a speed or parameter-count baseline.
Metrics:
- [s4] Bits per pixel measures bitrate.
- [s4] PSNR and MS-SSIM measure reconstructed image quality.
- [s4] BD-rate and BD-PSNR summarize rate-distortion differences.
- [s5] FLOPs and decoding latency measure computational complexity.
- [s8] CPU/GPU inference speed and parameter count are used in acceleration ablations.
Results:
- [s5] FFCA Table 1 BD-rate versus BPG: KITTI -74.62% PSNR, -85.18% MS-SSIM.
- [s5] FFCA Table 1 BD-rate versus BPG: Cityscapes -37.84% PSNR, -55.36% MS-SSIM.
- [s5] FFCA Table 1 BD-rate versus BPG: InStereo2K -47.02% PSNR, -69.75% MS-SSIM.
- [s5] Table 2 reports FFCA 781.76G FLOPs and 4.91s decoding time on InStereo2K at 832 x 1024.
- [s6] Table 3 reports Proposed FFCA BD-rate -54.51% and BD-PSNR 2.27dB in the ablation study.
- [s8] Table 4 reports Stereo PM speed of 0.76s CPU and 0.027s GPU, compared with Multi-scale PM at 15.32s CPU and 0.46s GPU.
- [s8] Table 5 reports Fast Feature Fusion at 1.84s CPU and 3.04M parameters.
- [s8] Table 6 reports hourglass-based sparse stereo refinement at 1.41s CPU and 0.24M parameters.
Stated limitations:
- [s7] The conclusion identifies extracting more general priors as a future direction to broaden applicability.
- [s7] The conclusion identifies more efficient use of priors for accelerating encoding and decoding as a future direction.
```

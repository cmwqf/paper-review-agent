# Paper Map

```text
PAPER MAP
Title: OpenMixup: A Comprehensive Mixup Benchmark for Visual Classification
Authors: Anonymous authors
Venue: ICLR 2024
Submission date: 2023-09-15

SECTIONS
[s1] Abstract and Introduction
Summary: The paper motivates the need for systematic, standardized evaluation of mixup data augmentation methods for supervised visual classification. It introduces OpenMixup as a unified benchmark and codebase for comparing mixup algorithms across varied datasets, architectures, metrics, and analysis tools.
Key items:
- problem: Existing mixup methods use diverse configurations and code styles, making impartial comparison and reproduction difficult.
- claim: OpenMixup is presented as the first comprehensive mixup visual classification benchmark.
- claim: The benchmark evaluates 16 representative mixup algorithms from scratch across 12 visual classification datasets.
- method_component: The framework includes data preprocessing, mixup algorithms, backbones, optimization policies, distributed training, and analysis toolkits.
- motivation: The paper focuses on supervised visual classification even though mixup is also used in semi-supervised, self-supervised, and downstream tasks.
- other (Figure 1): Top-1 accuracy radar plots summarize CNN-based mixup benchmark results across datasets.

[s2] Background and Related Work
Summary: This section defines mixup training for image classification and reformulates mixup as a sample-generation policy plus a label-mixing policy optimized for classification. It categorizes sample mixing methods into static and dynamic policies and describes label mixing strategies including Mixup, CutMix, attention-guided labels, and DecoupledMix.
Key items:
- method_component (Equation 2): Mixup training generates mixed samples x_mix and mixed labels y_mix using sample mixup function h, label mixup function g, and mixing ratio lambda drawn from Beta(alpha, alpha).
- method_component (Equation 3): The paper reformulates mixup generation as an auxiliary task with a parametric policy h_phi optimized jointly with classifier parameters theta.
- method_component (Table 1): Static sample mixing policies include Mixup, ManifoldMix, CutMix, SmoothMix, GridMix, ResizeMix, FMix, AttentiveMix, and SaliencyMix.
- method_component (Table 1): Dynamic sample mixing policies include PuzzleMix, AlignMix, AutoMix, SAMix, TransMix, SMMix, and related optimization-based or learnable approaches.
- method_component: Most label mixing uses Mixup or CutMix labels, while transformer-oriented methods use attention maps and DecoupledMix uses a decoupled learning objective.
- other (Figure 2): The paper visualizes supported mixup augmentation methods on ImageNet-1K at lambda equals 0.5.

[s3] OpenMixup Framework and Supported Methods
Summary: This section describes the PyTorch-based OpenMixup codebase, its modular OpenMMLab-style design, and the supported mixup methods and model architectures. It explains how components such as models, datasets, augmentations, configs, benchmarks, and tools are organized.
Key items:
- method_component: OpenMixup is implemented in PyTorch and follows an OpenMMLab-style modular structure referencing MMClassification.
- method_component (Figure 3): The codebase includes modules for model architecture, data preprocessing, mixup policies, script tools, configuration files, benchmark configs, and model zoos.
- method_component (Section 3.1): The framework supports 16 representative mixup augmentation algorithms and 19 CNN or Transformer model architectures.
- method_component (Table 1): Supported methods include Mixup, CutMix, SmoothMix, GridMix, ResizeMix, ManifoldMix, FMix, AttentiveMix, SaliencyMix, PuzzleMix, AlignMix, AutoMix, SAMix, TransMix, SMMix, and DecoupledMix.
- method_component (Table 1): Dynamic methods include optimal-transported policies, end-to-end learnable cutting policies, and attention-guided transformer-specific policies.
- other: Configuration files are used to customize datasets, mixup strategies, model architectures, and optimization schedules.

[s4] Supported Tasks, Metrics, and Experimental Pipeline
Summary: This section lists the datasets, task categories, metrics, empirical analysis tools, and workflow used by OpenMixup. The supported classification settings include small-scale, large-scale, fine-grained, long-tail, and scenic classification, with additional transfer evaluation for detection.
Key items:
- dataset (Table 2): Supported classification datasets include CIFAR-10, CIFAR-100, FashionMNIST, STL-10, Tiny-ImageNet, ImageNet-1K, CUB-200-2011, FGVC-Aircraft, iNaturalist2017, iNaturalist2018, and Places205.
- dataset (Section 3.3): Transfer evaluation uses COCO train2017 for object detection with Faster R-CNN and Mask R-CNN initialized from ImageNet-1K pretrained models.
- metric (Section 3.3): Performance metrics include top-1 accuracy, total training hours, GPU memory, corruption robustness, and transfer performance.
- metric (Section 3.3): Empirical analysis uses ECE calibration, CAM visualization, loss landscape visualization, training loss curves, and validation accuracy curves.
- method_component (Figure 5): The experimental pipeline selects dataset and preprocessing, builds the model, configures mixup and optimization, and runs distributed training and analysis tools.
- other: Documentation is provided through OpenMixup online user documents including installation, getting started, benchmark results, and related work lists.

[s5] Experiment and Analysis
Summary: This section reports benchmark experiments over small-scale datasets, ImageNet-1K, fine-grained datasets, long-tail datasets, scenic classification, and empirical analyses. It compares static and dynamic mixup methods under shared hyperparameter search and reports mean results over three trials.
Key items:
- baseline: Vanilla denotes the classification baseline without mixup augmentation.
- method_component: For fair comparison, the shared mixup hyperparameter alpha is searched over {0.1, 0.2, 0.5, 1, 2, 4}; other hyperparameters follow original papers.
- result (Table 3): On CIFAR-10, CIFAR-100, and Tiny-ImageNet examples in the main table, SAMix reports 97.50, 85.50, and 72.18 top-1 accuracy respectively.
- result (Table 4): On ImageNet-1K examples in the main table, SAMix reports 78.06 with PyTorch ResNet-50, 78.64 with RSB A3 ResNet-50, 73.42 with RSB A2 MobileNetV2, 80.94 with DeiT-S, and 81.87 with Swin-T.
- result (Table 5): The paper ranks SAMix first for performance, DeiT first for overall ranking, and Mixup/CutMix/DeiT/static variants highest for applicability.
- claim (Figure 6): The empirical observations state that dynamic mixup generally performs better than static mixup across datasets and backbones but requires more tuning and training cost.

[s6] Supplementary Implementation Details and Additional Benchmarks
Summary: The supplementary material provides installation commands, training settings, detailed ImageNet-1K recipes, small-scale classification results, downstream classification results, and transfer learning results. It also specifies how ranking scores are computed from performance, robustness, calibration, time usage, and generalizability.
Key items:
- method_component (Table A1): ImageNet-1K settings include PyTorch-style, DeiT, RSB A2, and RSB A3 recipes with specified epochs, optimizers, batch sizes, augmentation, and losses.
- result (Tables A2-A4): Additional ImageNet-1K results are reported for ResNet variants, transformer-based architectures, EfficientNet-B0, and MobileNetV2 under several training recipes.
- result (Tables A5-A9): Additional small-scale results cover CIFAR-10, CIFAR-100, Tiny-ImageNet, and CIFAR-100 robustness/calibration metrics.
- result (Table A10): Fine-grained and scenic classification results are reported on CUB-200, FGVC-Aircraft, iNaturalist2017, iNaturalist2018, and Places205.
- dataset (Section B.4): Transfer learning experiments use COCO-2017 for object detection and ADE20K for semantic segmentation.
- metric (Tables A11-A12): Transfer metrics include detection mAP, AP50, AP75, and segmentation mIoU.

[s7] Conclusion and Discussion
Summary: The paper concludes by reiterating OpenMixup as a comprehensive benchmark and modular codebase for mixup-based visual representation learning. It states limitations in the task scope and outlines future extensions to broader computer vision scenarios.
Key items:
- claim: The paper states that OpenMixup provides a standardized mixup benchmark and practical codebase platform for the mixup community.
- claim: The authors state that empirical analyses give observations and take-home messages for systematic understanding of mixup methods.
- stated_limitation: The scope is largely limited to representative visual classification tasks.
- stated_limitation: Although transfer learning to object detection and semantic segmentation is provided, broader task coverage is left for future work.
- other: The authors plan to extend OpenMixup to object detection, semantic segmentation, and self-supervised visual representation learning.

GLOBAL INDEX
Claims:
- [s1] OpenMixup is presented as the first comprehensive mixup visual classification benchmark.
- [s1] The benchmark evaluates 16 representative mixup algorithms across 12 visual classification datasets.
- [s5] Dynamic mixup is reported to generally perform better than static mixup across datasets and backbones, with higher tuning and training costs.
- [s7] The paper states that OpenMixup supplies a standardized benchmark and practical codebase for mixup research and use.
Method components:
- [s2] Mixup training uses sample mixing h, label mixing g, and Beta(alpha, alpha) mixing ratios with mixup cross-entropy.
- [s2] The reformulation treats mixup sample generation as a parametric auxiliary task h_phi optimized for classification.
- [s3] OpenMixup includes modular model, dataset, augmentation, config, benchmark, and tool components.
- [s3] Supported mixup methods include Mixup, CutMix, SmoothMix, GridMix, ResizeMix, ManifoldMix, FMix, AttentiveMix, SaliencyMix, PuzzleMix, AlignMix, AutoMix, SAMix, TransMix, SMMix, and DecoupledMix.
- [s4] The pipeline configures data preprocessing, model architecture, mixup policy, optimization schedule, and analysis tools.
Datasets:
- [s4] CIFAR-10, CIFAR-100, FashionMNIST, STL-10, Tiny-ImageNet, ImageNet-1K, CUB-200-2011, FGVC-Aircraft, iNaturalist2017, iNaturalist2018, and Places205 are listed as supported classification datasets.
- [s6] COCO-2017 is used for transfer experiments in object detection.
- [s6] ADE20K is used for transfer experiments in semantic segmentation.
- [s4] CIFAR-100-C and ImageNet-C are used for corruption robustness evaluation.
Baselines:
- [s5] Vanilla classification without mixup augmentation is used as a baseline.
- [s3] Mixup and CutMix are included as standard static mixup baselines.
- [s3] Other compared mixup baselines include ManifoldMix, SmoothMix, GridMix, ResizeMix, FMix, AttentiveMix, SaliencyMix, PuzzleMix, AlignMix, AutoMix, SAMix, TransMix, SMMix, DecoupledMix, and Co-Mixup/TokenMix in supplementary comparisons.
- [s5] Backbone baselines include ResNet, Wide-ResNet, ResNeXt, MobileNetV2, EfficientNet, DeiT, Swin, ConvNeXt, PVT, and MogaNet variants.
Metrics:
- [s4] Top-1 accuracy is the primary classification performance metric.
- [s4] Training overhead metrics include total training hours and GPU memory.
- [s4] Robustness is evaluated with corruption robustness on CIFAR-100-C and ImageNet-C and with FGSM in supplementary CIFAR-100 results.
- [s4] Calibration is measured with expected calibration error.
- [s4] Empirical analysis tools include CAM visualization, loss landscape, training loss curves, and validation accuracy curves.
- [s6] Transfer metrics include object detection mAP/AP50/AP75 and semantic segmentation mIoU.
Results:
- [s5] Main CIFAR/Tiny results show SAMix with the highest listed top-1 accuracies among shown methods: 97.50 on CIFAR-10, 85.50 on CIFAR-100, and 72.18 on Tiny-ImageNet.
- [s5] Main ImageNet-1K results show SAMix with 78.06 on PyTorch ResNet-50, 78.64 on RSB A3 ResNet-50, 73.42 on RSB A2 MobileNetV2, 80.94 on DeiT-S, and 81.87 on Swin-T.
- [s5] The take-home ranking table lists SAMix first in performance, DeiT first overall, and SMMix third overall.
- [s6] Supplementary transfer results report COCO detection and ADE20K segmentation performance for ImageNet-pretrained models using selected mixup policies.
- [s5] CAM visualizations are used to compare localization behavior for top-1 and top-2 predicted classes under supported mixup methods.
Stated limitations:
- [s7] The work is largely limited to the most representative visual classification tasks.
- [s7] Extension to object detection, semantic segmentation, and self-supervised visual representation learning is identified as future work.
```

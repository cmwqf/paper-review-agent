# Paper Map

```text
PAPER MAP
Title: APD: Boosting Adversarial Transferability via Perturbation Dropout
Authors: Anonymous authors
Venue: ICLR 2024
Submission date: 2023-09-17

SECTIONS
[s1] Abstract and Introduction
Summary: The paper studies black-box adversarial transferability and argues that perturbations spread over an image can depend on synergy across regions. It proposes Adversarial Perturbation Dropout (APD), which drops perturbation blocks during optimization and uses class activation maps to choose dropped regions. The introduction states that APD can be integrated with existing iterative attacks and reports improved attack success rates on ImageNet.
Key items:
- problem: Adversarial examples generated on a source model may not transfer well to unseen target models because attention regions differ across models.
- motivation (Figure 1): Existing perturbation extension strategies may rely on synergy among perturbations across regions, while target models may attend to only part of those perturbations.
- claim: Reducing mutual influence between perturbation regions can improve transferability when only partial perturbations fall in a target model's attention region.
- method_component: APD applies a dropout mechanism to perturbations during adversarial example optimization.
- method_component: Class activation maps are used to locate midpoints of dropped perturbation regions.
- result: The paper states that APD improves attack success rates when combined with existing methods, including improvements up to 19.6%.

[s2] Related Works
Summary: This section reviews adversarial example generation, black-box transfer attacks, and defenses against adversarial examples. It lists FGSM, PGD, I-FGSM, C&W, and transferability-enhancing methods, and describes defenses such as adversarial training, ensemble adversarial training, feature denoising, and NRP.
Key items:
- baseline: Discussed adversarial attack methods include FGSM, PGD, I-FGSM, and C&W.
- baseline: Discussed transferability methods include input diversity, momentum, translation-invariant attacks, scale-invariant attacks, intermediate-level attacks, reverse adversarial perturbation, and ghost networks.
- other: Discussed defenses include adversarial training, ensemble adversarial training, feature denoising, and NRP purification.
- problem: The paper focuses on image recognition attacks in black-box settings.

[s3] Methods: Notation and Existing Methods
Summary: This section defines the adversarial attack objective and perturbation constraint. It summarizes I-FGSM and MI-FGSM as existing iterative methods for generating adversarial examples.
Key items:
- method_component: The attack objective is to maximize classifier loss J(x_adv, y_true) while satisfying an L-infinity perturbation bound.
- metric: The perturbation constraint uses p = infinity with maximum per-pixel perturbation epsilon.
- baseline: I-FGSM iteratively updates adversarial examples using the sign of the gradient and clips within the epsilon ball.
- baseline (Equation 1): MI-FGSM adds a momentum term to the iterative gradient update.

[s4] Methods: Drop Region Selection and APD
Summary: This section motivates CAM-guided perturbation dropping and gives the APD optimization procedure. APD generates multiple dropped versions of the current adversarial image by replacing perturbation regions with clean-image content, computes gradients on these images, averages them, and updates the adversarial example.
Key items:
- claim (Figure 2): The paper argues that attention regions of a model are composed of a limited number of blocks and that synergies among perturbations in those blocks affect transferability.
- method_component: APD uses Grad-CAM++ at each attack iteration to identify CAM local maxima as centers of dropped regions.
- method_component: The number of region centers is limited to 3 in the described implementation.
- method_component: For each center, APD creates m dropped images using square regions with side lengths from beta to m beta.
- method_component (Algorithm 1): Dropped perturbation regions are replaced by the corresponding clean image regions before gradient computation.
- method_component: The APD update averages gradients over n times m dropped images and applies an I-FGSM-style clipped update.

[s5] Experiments: Setup
Summary: This section describes the ImageNet evaluation setup, source and target models, baselines, and hyperparameters. The evaluation uses 1000 ImageNet images and compares APD integrated with several attack methods.
Key items:
- dataset: Experiments use 1000 randomly chosen ImageNet images from 1000 categories that are almost correctly classified by all models.
- baseline: Normally trained models include Inc-v3, Inc-v4, IncRes-v2, and Res-101.
- baseline: Adversarially trained target models include Inc-v3_ens3, Inc-v3_ens4, and IncRes-v2_ens.
- baseline: Attack baselines include MI-FGSM, DIM, TIM, SIM, AAM, and AA-TI-DIM.
- metric: The main evaluation metric is attack success rate (ASR), defined as misclassification rate by target models.
- method_component: Default settings include epsilon = 16, T = 10, alpha = 1.6, MI-FGSM decay mu = 1.0, APD m = 5, and beta = 27.

[s6] Experiments: General Attacks
Summary: This section evaluates APD under single-source-model and ensemble-source-model attacks. APD is integrated with multiple baselines and compared on normally trained and adversarially trained target models.
Key items:
- result (Table 1): In single-model attacks, APD improves average black-box ASR over MI by 12.7%.
- result (Table 1): When integrated with DIM, TIM, SIM, AAM, and AA-TI-DIM, APD reports average improvements of 12.7%, 12.3%, 10.3%, 11.0%, and 6.8%, respectively.
- result (Table 1): The paper reports an average improvement of 12.74% on black-box normally trained models and 9.00% on adversarially trained models.
- method_component: Ensemble attacks fuse logit outputs of Inc-v3, Inc-v4, IncRes-v2, and Res-101.
- result (Table 2): In the ensemble-model attack setting, APD boosts transferability by an average of 15.62% in black-box settings.

[s7] Experiments: Defense Models, Diverse Architectures, and Ablations
Summary: This section evaluates APD-AA-TI-DIM on defense models and diverse architectures, and presents ablations for region selection, beta, number of centers, and number of scales. It also includes appendix analyses of perturbation synergy, cutout comparison, and same-computation comparison.
Key items:
- baseline (Table 3): Defense evaluations include ResNeXt_DA, Res152_D, NRP, and NRP_resG.
- baseline (Table 3): Diverse architecture targets include Seq2d_l, ViT-B/16, and MnasNet.
- result (Table 3): APD-AA-TI-DIM exceeds AA-TI-DIM by 2.6% average ASR on the evaluated defense models.
- result (Table 3): APD-AA-TI-DIM exceeds AA-TI-DIM by 13.3%, 11.3%, and 1.8% on Seq2d_l, ViT-B/16, and MnasNet, respectively.
- ablation (Figure 4): CAM-based region selection is compared with random region selection and reports stronger transferability for CAM-based APD.
- ablation (Figures 5 and 6): Ablations test beta values from 3 to 33, number of centers, and number of scales; beta = 27 is reported as the best or near-best in most tested conditions.

[s8] Conclusion and Appendix
Summary: The conclusion restates APD as a perturbation dropout method for improving adversarial transferability by reducing interaction across attention-region perturbations. The appendix provides analyses of perturbation synergy, a cutout comparison, a same-computational-cost comparison, and full pseudocode.
Key items:
- claim: APD is presented as offering a perspective of improving transferability by reducing interaction between different perturbation regions.
- result (Figure 7): Removing perturbations at CAM attention blocks causes larger reduction in attack success than random perturbation removal in the appendix analysis.
- ablation (Figure 8): APD is compared with a cutout variant that fills dropped regions with zeros, and APD reports stronger transferability.
- stated_limitation (Appendix A.3): The paper notes that APD has additional computational cost compared with original I-FGSM.
- result (Table 4): With the same-computation discussion, MI-FGSM with 15 times iterations only slightly improves transferability in limited cases, while APD-MI reports larger gains.
- method_component (Algorithm 1): The appendix provides full pseudocode for the APD attack algorithm.

GLOBAL INDEX
Claims:
- [s1] Synergy among perturbation regions may reduce adversarial transferability when target models attend to only part of the perturbation.
- [s1] Perturbation dropout can increase independence of perturbations across attention regions and improve black-box transferability.
- [s4] Attention regions are described as a limited set of blocks, and perturbation synergies in those blocks are claimed to affect transferability.
- [s8] Reducing interaction between different perturbation regions is presented as a way to produce perturbations that transfer to target models.
Method components:
- [s3] Adversarial examples are optimized under an L-infinity perturbation bound.
- [s4] APD applies perturbation dropout during iterative adversarial optimization.
- [s4] Grad-CAM++ is used at each iteration to find CAM local maxima as drop-region centers.
- [s4] For each center, APD drops square regions at multiple scales and averages gradients over the dropped images.
- [s4] Dropped regions are replaced with clean-image pixels, not zeros, in the main APD method.
- [s6] APD is integrated with attacks such as MI, DIM, TIM, SIM, AAM, and AA-TI-DIM.
Datasets:
- [s5] ImageNet, using 1000 randomly selected images from 1000 categories.
Baselines:
- [s2] FGSM, PGD, I-FGSM, and C&W are reviewed as adversarial attack methods.
- [s5] Attack baselines: MI-FGSM, DIM, TIM, SIM, AAM, and AA-TI-DIM.
- [s5] Normally trained models: Inc-v3, Inc-v4, IncRes-v2, and Res-101.
- [s5] Adversarially trained models: Inc-v3_ens3, Inc-v3_ens4, and IncRes-v2_ens.
- [s7] Defense and diverse targets: ResNeXt_DA, Res152_D, NRP, NRP_resG, Seq2d_l, ViT-B/16, and MnasNet.
Ablations:
- [s7] CAM-based drop-region selection versus random drop-region selection.
- [s7] Scale parameter beta varied from 3 to 33.
- [s7] Number of CAM centers and number of region scales varied.
- [s8] APD compared with cutout-style dropping that fills dropped regions with zeros.
- [s8] APD-MI compared with MI-FGSM using 1x and 15x iterations.
Metrics:
- [s5] Attack success rate (ASR), the misclassification rate on target models.
- [s3] L-infinity perturbation budget epsilon.
Results:
- [s6] Single-model attacks: APD improves average black-box ASR over MI by 12.7%.
- [s6] Single-model attacks: APD integration improves DIM, TIM, SIM, AAM, and AA-TI-DIM by 12.7%, 12.3%, 10.3%, 11.0%, and 6.8% on average.
- [s6] The paper reports average improvements of 12.74% on black-box normally trained models and 9.00% on adversarially trained models.
- [s6] Ensemble-model attacks: APD improves black-box transferability by an average of 15.62%.
- [s7] Defense models: APD-AA-TI-DIM improves average ASR over AA-TI-DIM by 2.6%.
- [s7] Diverse architectures: APD-AA-TI-DIM improves ASR over AA-TI-DIM by 13.3% on Seq2d_l, 11.3% on ViT-B/16, and 1.8% on MnasNet.
- [s8] Appendix results report that CAM attention-block perturbation removal reduces ASR more than random removal, APD outperforms cutout, and APD-MI outperforms higher-iteration MI-FGSM in Table 4.
Stated limitations:
- [s8] APD has additional computational cost compared with original I-FGSM.
```

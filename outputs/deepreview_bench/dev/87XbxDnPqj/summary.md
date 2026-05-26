# Paper Map

```text
PAPER MAP
Title: Gradient Descent Provably Solves Nonlinear Tomographic Reconstruction
Authors: Anonymous authors
Venue: ICLR 2024
Submission date: 2023-10-06

SECTIONS
[s1] Abstract and Introduction
Summary: This section motivates direct reconstruction from raw nonlinear CT measurements governed by the Beer-Lambert law, instead of applying logarithmic preprocessing to obtain a linear Radon model. It states that the logarithm becomes ill-conditioned near complete X-ray absorption, especially around metal or in low-dose scans. The section lists theoretical convergence results and 3D cone-beam CT experiments as the main contributions.
Key items:
- problem (Section 1): Linearized CT preprocessing uses −ln(1−y), which is numerically unstable when raw measurements approach one.
- motivation (Section 1): High-density materials such as metal implants can produce streak artifacts under linearized reconstruction.
- method_component (Equation 1.2): The paper studies direct least-squares optimization through the nonlinear model y_i = 1 − exp(−a_i^T x).
- claim: Gradient descent is claimed to converge geometrically to the global optimum despite the nonconvex objective.
- claim: The regularized setting is claimed to recover structured signals with sample complexity matching the relevant statistical dimension up to constants.
- result: Experiments are reported on synthetic and real 3D cone-beam CT volumes, including a skull with metal dental crowns.

[s2] Problem Formulation
Summary: This section defines the theoretical nonlinear measurement model using i.i.d. Gaussian measurement vectors and a ReLU inside the Beer-Lambert nonlinearity. It introduces the least-squares loss, subgradient descent from zero initialization, and a regularized loss for compressive sensing. It also explains how the Gaussian model is connected to ray-structured CT measurements and shows empirical positivity of a pseudoconvexity correlation for the true ray model.
Key items:
- method_component (Equation 2.1): The theoretical model uses y_i = f(a_i^T x), where f(u)=1−exp(−u_+) and a_i are i.i.d. N(0,I_n).
- method_component (Equation 2.2): The unregularized objective is a least-squares loss over nonlinear measurements.
- method_component: Subgradient descent starts from z_0=0 and uses the specified subdifferential of f, including f'(0)=1/2.
- method_component (Equation 2.3): The regularized/compressive version adds λR(z); experiments use 3D total variation as R.
- stated_limitation: The theoretical analysis replaces sparse nonnegative ray-structured CT measurement vectors with Gaussian measurement vectors.
- result (Figure 1): The paper reports empirical positivity of the key gradient-error correlation for the true projection-based loss.

[s3] Global Convergence in the Unregularized Setting
Summary: This section states Theorem 1 for exact recovery from nonlinear Gaussian measurements without regularization. The theorem gives a measurement requirement proportional to n with exponential dependence on the signal norm and proves geometric convergence from zero initialization with specified step sizes. The section also describes estimating the unknown signal norm from the average measurement value.
Key items:
- claim (Theorem 1): For Gaussian nonlinear CT measurements, gradient descent globally recovers the true signal at a geometric rate.
- result (Theorem 1): Theorem 1 requires m at least proportional to exp(c||x||_2)/||x||_2^2 times n.
- metric (Theorem 1): The convergence guarantee bounds squared ℓ2 reconstruction error ||z_t−x||_2^2.
- result (Theorem 1): The stated convergence rate is geometric with factor 1−μ exp(−10||x||_2).
- method_component (Theorem 1): The first step size depends on ||x||_2 through an expression involving the complementary error function.
- stated_limitation: The convergence rate and sample complexity depend exponentially on ||x||_2 because measurements saturate as density increases.

[s4] Global Convergence in the Regularized Setting
Summary: This section extends the analysis to compressive sensing with structured signals and convex regularizers. It formulates constrained nonlinear least squares, defines the descent cone, Gaussian width, and minimal sample function m0, and states Theorem 2. The theorem gives geometric convergence for projected gradient descent with sample complexity proportional to m0 up to signal-norm-dependent factors.
Key items:
- method_component (Equation 4.1): The constrained optimization minimizes nonlinear least squares subject to R(z) ≤ R(x).
- method_component (Equations 4.2 and 4.3): The algorithm is projected gradient descent onto K={z: R(z) ≤ R(x)}.
- method_component (Definitions 1-3): The section defines descent sets, descent cones, Gaussian width, and m0 as the squared Gaussian width of the restricted descent cone.
- claim (Theorem 2): Theorem 2 applies to any convex regularizer and arbitrary signal structure captured by that regularizer.
- result (Theorem 2): Theorem 2 requires m at least proportional to exp(c||x||_2)/||x||_2^2 times m0.
- result: For an s-sparse signal with ℓ1 regularization, the stated sample complexity scales as s log(n/s).

[s5] Experiments
Summary: This section reports 3D cone-beam CT experiments implemented with a JAX Plenoxels-based dense 3D grid and mild total variation regularization. Synthetic experiments use a modified 3D Shepp-Logan phantom with a density-varied ellipsoid and compare linearized versus nonlinear reconstruction. Real experiments use CBCT measurements of a human skull with metal dental crowns and compare nonlinear reconstruction to commercial linearized reconstruction and FDK.
Key items:
- dataset: Synthetic data are generated from a modified 3D Shepp-Logan phantom with scaled voxel densities and one density-varied ellipsoid.
- dataset: Real data are CBCT measurements of a human skull containing metal dental crowns.
- baseline: Synthetic comparisons include reconstruction after logarithmic linearization using the linear forward model.
- baseline (Figure 3): Real comparisons include a commercial linearized reconstruction and the FDK baseline.
- metric (Figure 2): PSNR is reported for synthetic reconstructions, defined as −10 log10(MSE) over the full volume.
- result (Figures 2 and 3): Nonlinear reconstruction is reported to reduce metal artifacts compared with linearized reconstruction in synthetic and real CBCT examples.

[s6] Related Work
Summary: This section situates the paper among CT reconstruction methods, compressive sensing and regularized reconstruction, neural CT reconstruction methods, photon-counting CT, and nonlinear measurement recovery. It states that standard CT methods often rely on the linear Radon model and that prior work on nonlinear measurements covers phase retrieval, ReLU models, and other nonlinearities. The section contrasts the paper’s activation and structured recovery setting with cited nonlinear recovery results.
Key items:
- baseline: Filtered Back Projection is described as a closed-form inverse for the Radon transform and a standard CT option.
- baseline: ISTA and FISTA are cited as iterative methods for convex regularized CT reconstruction.
- baseline: Neural adaptive tomography and data-driven priors are cited as deep learning approaches for limited-measurement CT reconstruction.
- other: Photon-counting CT scanners are described as measuring raw X-ray photon counts and potentially supporting nonlinear reconstruction and noise modeling.
- claim: The paper states that cited neural and regularized CT methods are still based on the linear measurement model.
- claim: The paper states that its nonlinear recovery result handles a non-differentiable activation, arbitrary signal structures, and any convex regularizer.

[s7] Discussion
Summary: This section recaps the motivation for avoiding logarithmic preprocessing and summarizes the theoretical and experimental findings. It reiterates exact recovery and geometric convergence for nonlinear raw-measurement reconstruction, including a compressive sensing extension. It identifies more realistic measurement noise models, especially Poisson noise, as future work.
Key items:
- claim: The paper concludes that direct nonlinear reconstruction avoids an unstable preprocessing step at the cost of nonconvex least squares.
- result: The discussion restates that the unregularized nonlinear problem uses order n measurements, matching linear forward-model sample complexity in order.
- result: The discussion restates that structural regularization allows reconstruction with far fewer than n measurements.
- result: The discussion states that nonlinear reconstruction reduced metal artifacts in both synthetic and real 3D cone-beam CT experiments.
- stated_limitation: Future work may extend the theory and experiments to more realistic measurement noise settings such as Poisson noise.

[s8] Appendices: Proofs of Theorems 1 and 2
Summary: The appendices provide proof outlines and details for the unregularized and regularized convergence theorems. The proofs use a first-step neighborhood argument, local pseudoconvexity/correlation lower bounds, a gradient smoothness bound, and induction for geometric convergence. The regularized proof modifies the unregularized argument by replacing dimension n with the minimal sample parameter m0 in concentration terms.
Key items:
- method_component (Appendix B.1): The proof of Theorem 1 has four steps: first iteration near x, local pseudoconvexity, smoothness, and a contraction argument.
- result (Appendix B.2): The first-step analysis shows z_1 enters a ball of radius one quarter of ||x||_2 under sufficient measurements.
- method_component (Appendices B.3 and B.4): Local pseudoconvexity is proved via lower bounds on the gradient-error correlation in two angular cases.
- method_component (Appendix B.5): The smoothness step bounds ||∇L(z)||_2 by a constant times ||z−x||_2 using the operator norm of the Gaussian measurement matrix.
- method_component (Appendix C): The proof of Theorem 2 uses the descent cone and replaces n by m0 in concentration bounds.

GLOBAL INDEX
Claims:
- [s1] Direct nonlinear reconstruction is proposed as an alternative to logarithmic preprocessing for CT measurements near saturation.
- [s1] Gradient descent is claimed to converge globally at a geometric rate for the nonlinear CT objective under the Gaussian model.
- [s4] Projected gradient descent with any convex regularizer is claimed to recover structured signals from a number of nonlinear measurements proportional to m0 up to signal-norm factors.
- [s6] The paper states that its nonlinear recovery setting handles a non-differentiable activation, arbitrary signal structures, and any convex regularizer.
Method components:
- [s1] Nonlinear Beer-Lambert measurement model y_i = 1−exp(−a_i^T x).
- [s2] Gaussian theoretical model with ReLU-wrapped inner product f(u)=1−exp(−u_+).
- [s2] Unregularized nonlinear least-squares loss optimized with subgradient descent from zero.
- [s2] Regularized loss with λR(z), using 3D total variation in experiments.
- [s4] Constrained nonlinear least squares with projected gradient descent onto R(z) ≤ R(x).
- [s8] Proof strategy based on first-step concentration, pseudoconvexity, smoothness, and contraction.
Datasets:
- [s5] Modified 3D Shepp-Logan phantom with one ellipsoid varied from soft-tissue-like to bone-like to metal-like density.
- [s5] Real cone-beam CT measurements of a human skull with metal dental crowns.
Baselines:
- [s5] Linearized reconstruction using logarithmic preprocessing and the linear forward model.
- [s5] Commercial linearized reconstruction for the real skull dataset.
- [s5] FDK reconstruction baseline for the real skull dataset.
- [s6] Filtered Back Projection, ISTA, FISTA, and neural CT reconstruction methods are discussed as related CT reconstruction approaches.
Metrics:
- [s3] Squared ℓ2 reconstruction error ||z_t−x||_2^2 in theoretical convergence bounds.
- [s5] PSNR over the whole synthetic volume, defined as −10 log10(MSE).
- [s2] Empirical gradient-error correlation ∇L(z)^T(z−x)/||z−x||_2^2 used to illustrate pseudoconvexity.
Results:
- [s3] Theorem 1 gives geometric convergence in the unregularized Gaussian setting with m on the order of n times a signal-norm-dependent factor.
- [s4] Theorem 2 gives geometric convergence in the regularized setting with m on the order of m0 times a signal-norm-dependent factor.
- [s4] For s-sparse signals with ℓ1 regularization, the paper states sample complexity of order s log(n/s).
- [s5] Synthetic experiments report that nonlinear reconstruction remains close to the ground truth as the ellipsoid density increases, while linearized reconstruction shows increasing artifacts.
- [s5] Real skull experiments report fewer visible metal artifacts for nonlinear reconstruction than for the shown commercial linearized and FDK reconstructions.
- [s8] Appendix proof results include entry into a local neighborhood after the first step and local pseudoconvexity/smoothness sufficient for contraction.
Stated limitations:
- [s2] The theoretical model uses Gaussian measurements instead of true sparse, nonnegative, ray-structured CT measurement vectors.
- [s2] The theoretical analysis focuses on the noiseless setting, while the least-squares loss corresponds to Gaussian noise.
- [s3] The convergence rate and sample complexity have exponential dependence on ||x||_2 because measurements saturate for very dense signals.
- [s5] The experiments do not focus on speed or measurement sparsity.
- [s5] No ground truth is available for the real skull volume, so real-data comparison uses reference reconstructions.
- [s7] Future work is stated to include more realistic noise models such as Poisson noise.
```

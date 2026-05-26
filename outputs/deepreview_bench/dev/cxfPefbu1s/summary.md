# Paper Map

```text
PAPER MAP
Title: Procedural Fairness Through Decoupling Objectionable Data Generating Components
Authors: Zeyu Tang, Jialu Wang, Yang Liu, Peter Spirtes, Kun Zhang
Venue: ICLR 2024
Submission date: 2023-11-05

SECTIONS
[s1] Introduction
Summary: The paper defines procedural fairness as fairness requirements on the data generating process itself. It introduces disguised procedural unfairness as inadvertent alteration of neutral process components or lack of assurance that outcomes benefit least advantaged individuals. It proposes decoupling objectionable data generating components using reference points and a value instantiation rule.
Key items:
- problem: Existing causal fairness notions often quantify causal effects on outcomes while under-characterizing properties of the process itself.
- motivation: The framework is motivated by Rawlsian pure procedural justice and requirements on the procedure rather than only on outcomes.
- claim: Disguised procedural unfairness can occur when neutral components of a data generating process are altered while mitigating objectionable components.
- method_component: Objectionable components may be edges or path segments and are not limited to protected-feature-to-outcome paths.
- claim: The proposed approach makes predictions only based on neutral components after decoupling objectionable ones.

[s2] Preliminaries
Summary: This section introduces notation for variables, values, domains, causal graphs, directed edges, and parent nodes. It states two procedural fairness requirements: Fair Equality of Opportunity and the Difference Principle.
Key items:
- method_component: Data generating processes are represented with DAGs whose edges are atomic units of objectionable or neutral components.
- motivation: Procedural fairness is linked to Rawlsian pure procedural justice, where the procedure itself must satisfy fairness requirements.
- claim (Section 2.2): Fair Equality of Opportunity prohibits influence from arbitrary contingencies for those with the same talent, ability, and willingness.
- claim (Section 2.2): The Difference Principle requires inequalities to be arranged to the greatest benefit of the least advantaged members.
- claim: The paper treats these requirements as mandates on data generating processes rather than standalone criteria for predicted outcomes.

[s3] Illustrating Disguised Procedural Unfairness
Summary: This section uses a linear causal model from prior work to show how enforcing causal fairness constraints can alter neutral components. It compares parameter behavior under constraints associated with previous causal fairness approaches and discusses Requirement I violations.
Key items:
- method_component (Equation 1): The illustrative model has variables A, C, M, L, and Y with linear structural equations and Gaussian noise.
- metric (Equation 2): The path-specific effect is expressed as theta_A^Y plus theta_A^M times theta_M^Y plus theta_L^Y theta_M^L.
- baseline (Figure 1): The section discusses constraints from Kilbertus et al. and Nabi & Shpitser-style causal fairness approaches.
- result (Figure 1): Fitted parameters for neutral components can deviate from ground truth when fairness constraints are imposed on objectionable paths.
- claim: Arbitrary deviations in neutral components violate Requirement I because such components are affected by arbitrary contingencies.

[s4] Decoupling Objectionable Components for Procedural Fairness
Summary: This section develops the proposed framework. It first considers a simple parameter-dropping approach for the linear example, then presents local causal modules, reference points, the value instantiation rule, aggregation over the DAG, and optimization of reference points for least advantaged individuals.
Key items:
- method_component (Definition 4.1): Reference points are fixed values propagated along objectionable edges, assigned only when a node is the tail of an objectionable component.
- method_component (Algorithm 1): The value instantiation rule sets each local-module input to a reference point, a downstream value of reference points, or its original data value.
- method_component (Algorithm 2): Local causal modules are learned without fairness constraints, then aggregated in topological order while applying the value instantiation rule.
- method_component (Equation 3): The prediction is formed as a composition of fitted local modules and the ReferencePoint configuration.
- method_component (Equation 4): ReferencePoint is configured by maximizing expected predicted outcome for least advantaged individuals over domains of tail nodes of objectionable edges.
- stated_limitation: The paper notes that directly correcting causal mechanisms is not always viable because neutral versions of functional forms may be unavailable.

[s5] Experiments
Summary: The experiments evaluate the framework on a simulated linear example and the UCI Adult dataset in the main paper. The simulated example is used to demonstrate Requirement II violations, and UCI Adult compares approval-rate changes under path-specific counterfactual fairness and the proposed reference-point framework.
Key items:
- dataset (Section 5.1): Simulated linear data based on the A, C, M, L, Y model is used to study decision thresholds and group outcomes.
- baseline (Figure 2(a)): Simulated-data comparisons include unconstrained linear regression, No Unresolved Discrimination, and Fair Inference on Outcome-style constraints.
- metric (Figure 2(a)): Experiments report approval rates and group proportions among individuals rejected or accepted by all policies across decision thresholds.
- result (Figure 2(a)): In the simulated example, disadvantaged individuals proportionally suffer more among those rejected by all policies and prosper less among those accepted by all policies.
- dataset (Section 5.2): UCI Adult is used to predict whether annual income exceeds USD 50,000, with sex, age/native country, marital status, education, work attributes, and income.
- result (Figure 2(c)): On UCI Adult, the proposed framework increases approval rates for least advantaged individuals relative to the unconstrained baseline under reported reference-point configurations.

[s6] Concluding Remarks, Ethics Statement, and Reproducibility Statement
Summary: The conclusion restates the focus on procedural fairness for data generating processes and the proposed use of reference points with value instantiation. It also states ethical motivation and provides a GitHub repository for implementation.
Key items:
- claim: Previous approaches may violate Requirement I by altering neutral components and Requirement II by not arranging inequalities to benefit least advantaged individuals.
- claim: Decoupling objectionable data generating components is presented as necessary for procedural fairness.
- stated_limitation: Future work includes developing efficient and effective decoupling strategies when additional knowledge or assumptions about the process are available.
- other: The authors state adherence to the ICLR Code of Ethics and frame the work as promoting procedural guarantees on fairness.
- other (Reproducibility Statement): Implementation is provided at https://github.com/zeyutang/DecoupleObjectionable.

[s7] Appendices A-C: Related Work, Comparisons, and Framework Illustration
Summary: The appendices review causal fairness notions, responsive-agent settings, and fair representation learning. They also compare the proposed approach with prior work and provide a worked example of reference points and value instantiation across local causal modules.
Key items:
- baseline (Table 1): Related work includes conditional-independence fairness, path-specific interventional effects, counterfactual effects, recourse, intersectional subgroups, and fair representations.
- claim (Appendix B.1): The paper distinguishes counter-factual analysis with respect to variables from counter-factual analysis with respect to local causal mechanisms.
- method_component (Appendix B.2): Reference points are described as decision-maker-side input values for objectionable components, not as agent responses to a policy.
- method_component (Appendix B.3): The approach is characterized as modular decoupling of objectionable components rather than holistic fair representation learning.
- method_component (Appendix C): The worked example shows that the same node may receive different reference points for different objectionable outgoing edges.

[s8] Appendix D-E: Experiment Details, Additional Results, and Discussions
Summary: The later appendices give implementation details, scalability measurements, simulated-data details, UCI Adult details, and Folktables public health coverage experiments. They also discuss implications, procedural versus outcome emphasis, and potential limitations and future work.
Key items:
- method_component (Appendix D.1.1): Local causal modules are implemented as neural networks with two hidden layers, batch normalization, and SELU activations.
- method_component (Appendix D.1.1): Simulated annealing is used to derive ReferencePoint configurations that maximize benefit for least advantaged individuals.
- result (Table 2): A scalability example with 1,024 variables reports forward-pass computational costs comparable to a vanilla regressor.
- dataset (Appendix D.4): Additional experiments use Folktables 2021 ACS PUMS public health coverage prediction for CA, FL, and NY.
- result (Table 4): Folktables experiments report that different states can require different reference-point configurations under the same causal graph and least-advantaged-group criterion.
- stated_limitation (Section 4.2.1): Dynamic settings and directed cyclic graphs are stated to be beyond the scope of the current work.

GLOBAL INDEX
Claims:
- [s1] Disguised procedural unfairness is an overlooked issue involving altered neutral components or insufficient benefit to least advantaged individuals.
- [s2] Procedural fairness requirements are treated as mandates on the data generating process, not only on predicted outcomes.
- [s3] Causal fairness constraints can introduce arbitrary deviations in neutral components and thereby violate Requirement I.
- [s4] Reference points and value instantiation can decouple objectionable components while keeping neutral components intact.
- [s5] The simulated example is used to show Requirement II violation under compared causal fairness policies.
- [s6] The authors state that decoupling objectionable data generating components is important for achieving procedural fairness.
Method components:
- [s2] DAG representation of data generating process with directed edges as atomic objectionable or neutral components.
- [s4] Reference point: a fixed value propagated along an objectionable edge from its tail node.
- [s4] Value instantiation rule for local causal modules.
- [s4] Aggregation of local causal modules in topological order without fairness-constrained parameter fitting.
- [s4] Optimization of ReferencePoint mapping to maximize expected predicted outcome for least advantaged individuals.
- [s8] Neural-network local modules and simulated annealing for reference-point search in experiments.
Datasets:
- [s5] Simulated linear dataset with variables A, C, M, L, and Y.
- [s5] UCI Adult dataset for income above USD 50,000 prediction.
- [s8] Folktables 2021 ACS PUMS public health coverage prediction task for CA, FL, and NY.
Baselines:
- [s3] Kilbertus et al. causal fairness constraints for direct and proxy discrimination.
- [s3] Nabi & Shpitser-style path-specific effect constrained optimization or sufficient conditions.
- [s5] Unconstrained optimized baseline models.
- [s5] Path-Specific Counterfactual Fairness from Chiappa on UCI Adult.
- [s8] Vanilla regressor used for computational-cost comparison.
Ablations:
- [s5] UCI Adult experiments compare reference-point configurations of different strengths according to the number of decoupled objectionable components.
- [s8] UCI Adult appendix compares cases with objectionable components A to Y; A to Y and M to Y; plus M to R; plus M to L.
- [s8] Scalability example compares the proposed local-module forward pass with a vanilla regressor.
Metrics:
- [s3] Path-specific effect expression for objectionable paths.
- [s3] Signed relative deviation of fitted parameters from ground truth in the linear example.
- [s5] Approval rate and group-wise approval-rate changes.
- [s5] Group proportions among individuals accepted or rejected by all decision policies.
- [s8] Number of parameters and multiplier-accumulator operations for scalability comparison.
Results:
- [s3] Fairness constraints in the linear example lead to deviations in neutral fitted parameters.
- [s5] In the simulated threshold analysis, disadvantaged individuals are overrepresented among all-policy rejections and underrepresented among all-policy acceptances in reported cases.
- [s5] On UCI Adult, Path-Specific Counterfactual Fairness with sex flipping decreases approval rates for least advantaged individuals in the reported comparison.
- [s5] On UCI Adult, the proposed framework boosts approval rates for least advantaged individuals under reported reference-point configurations.
- [s8] The scalability example reports comparable forward-pass costs to a vanilla regressor for a 1,024-variable causal model.
- [s8] Folktables reference-point configurations differ by state even under shared graph and least-advantaged criteria.
Stated limitations:
- [s4] Direct correction of the causal mechanism may be unavailable when the neutral form of an objectionable component is unknown.
- [s4] The paper states that dynamic settings or directed cyclic graphs are beyond the scope of the current work.
- [s6] Future work includes developing efficient and effective decoupling strategies using additional knowledge or assumptions about the process.
- [s8] The appendix discusses potential limitations and future works, including broader implications of procedural versus outcome emphasis.
```

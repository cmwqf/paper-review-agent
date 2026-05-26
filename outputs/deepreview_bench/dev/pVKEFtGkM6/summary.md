# Paper Map

```text
PAPER MAP
Title: Investigating Uncertainty Calibration of Aligned Language Models under the Multiple-Choice Setting
Authors: Anonymous authors
Venue: ICLR 2024
Submission date: 2023-10-18

SECTIONS
[s1] Introduction
Summary: The paper studies logit-based uncertainty calibration of aligned language models under multiple-choice questions. It motivates the problem by noting that aligned LMs are often more overconfident than their pre-trained counterparts and states three goals: compare calibration behavior, analyze alignment effects through two uncertainties, and propose a few-shot post-hoc calibration method.
Key items:
- problem: Aligned LMs tend to be overconfident in output answers compared with corresponding pre-trained LMs.
- claim: In-context learning helps pre-trained LMs calibrate by demonstrating the response format.
- claim: Aligned LMs are overconfident with altered predictive distributions on both answer decision and response format.
- method_component: The paper defines answer uncertainty and format uncertainty for multiple-choice LM calibration.
- method_component: The paper proposes task-specific temperature scaling using the predictive distribution of the corresponding pre-trained LM.
- result: The proposed post-hoc method is reported to calibrate aligned LMs effectively with few-shot examples per task.

[s2] Background and Uncertainty Calibration of LMs under Multiple-Choice Setting
Summary: This section reviews pre-trained causal LMs, in-context learning, SFT, and learning from pairwise feedback. It formalizes multiple-choice logit-based uncertainty quantification using choice-letter probabilities and defines accuracy, confidence, and ECE with 10 bins.
Key items:
- method_component (Figure 2): Multiple-choice samples are formatted into an MCQ prompt with candidate answers mapped to choice letters.
- metric: Prediction is the choice letter with maximum probability at the target generation position.
- metric: Confidence is the maximum choice-letter probability from the token logits.
- metric (Equation 1): Calibration is measured with expected calibration error using 10 equal-sized bins.
- method_component: Alignment background includes supervised fine-tuning on instruction-response pairs and LPF through RLHF or preference-based cross-entropy losses.

[s3] How Pre-trained and Aligned LMs Differ in Calibration
Summary: This section empirically compares calibration of pre-trained Llama/Llama-2 models and aligned Vicuna/Llama-2-Chat models in zero-shot and five-shot settings. It evaluates seven multiple-choice tasks under two choice formats and analyzes accuracy, ECE, confidence, choice-letter probability mass, and format-identifier probability.
Key items:
- dataset (Section 3.1): Tasks include HellaSWAG, OpenbookQA, TruthfulQA, LogiQA, MMLU, CivilComments, and IMDB.
- baseline (Section 3.1): Pre-trained models are Llama and Llama-2 from 7B to 70B; aligned models are Vicuna and Llama-2-Chat.
- ablation (Section 3.1): Evaluation compares zero-shot learning and five-shot in-context learning, and choice formats "A" and "(A)".
- result (Figure 3): Pre-trained LMs show much lower ECE with larger capacity and few-shot examples; ZSL-to-ICL ECE gaps are especially large for large models.
- result (Figure 3): Aligned LMs have higher ECE than corresponding pre-trained models, and their accuracy and ECE change less between ZSL and ICL.
- result (Figure 4): For pre-trained LMs, the format identifier separates format preference from choice-letter probabilities; aligned LMs prefer directly outputting choice letters and remain overconfident in ZSL and ICL.

[s4] How Alignment Process Impacts LMs' Uncertainty Calibration
Summary: This section formalizes answer uncertainty and format uncertainty, studies common SFT and LPF alignment stages, and then uses synthetic alignment schemes to isolate effects on the two uncertainties. It concludes that altered answer uncertainty during alignment is a main source of overconfidence in multiple-choice calibration.
Key items:
- method_component (Section 4.1): Answer uncertainty represents choosing among candidates; format uncertainty represents preference over response formats.
- method_component (Equation 2): The predictive probability is decomposed into answer probability conditioned on format and format probability.
- claim (Assumption 4.1): For MCQs, once format uncertainty is eliminated toward the MCQ format, pre-trained LMs' answer uncertainty is assumed to be well-calibrated.
- ablation (Section 4.2): Alignment-stage study tracks pre-trained, SFT, and LPF checkpoints for Alpaca-Farm and Zephyr pipelines.
- ablation (Section 4.3): Synthetic schemes include SFT-Format, SFT-Choice, SFT-Mixed, DPO-Format, DPO-Choice, and DPO-Mixed.
- result (Figure 7): Format-only synthetic alignment preserves MMLU calibration close to pre-trained ICL, while Choice and Mixed schemes lead to overconfidence; DPO-Choice is reported as the most severe case.

[s5] Few-shot Post-hoc Calibration for Aligned Language Models
Summary: This section presents post-hoc calibration for aligned LMs using five hold-out examples per task. It compares few-shot temperature scaling, KDE, a constant-temperature baseline, and the proposed temperature scaling objective that matches the pre-trained LM's predictive distribution.
Key items:
- baseline (Equation 4): Temperature Scaling learns a scalar temperature by minimizing negative log likelihood on a calibration set.
- baseline (Equation 5): KDE refines confidence using estimated densities for correctly and incorrectly predicted calibration examples.
- baseline: A constant temperature T = 2.5 from prior work is used as a baseline.
- method_component (Equation 6): The proposed method minimizes KL divergence between the pre-trained LM predictive distribution and the temperature-scaled aligned LM distribution.
- result (Figure 8): On Llama-2-Chat 70B, the proposed method is the only method reported to improve over out-of-the-box calibration on all tasks and is most effective in most scenarios.
- stated_limitation: The proposed method requires access to the aligned LM's pre-trained counterpart and relies on strong calibration of that pre-trained LM across tasks.

[s6] Related Work and Conclusions
Summary: The related work section situates the paper among logit-based, semantic-based, and linguistic-based uncertainty estimation for LMs. The conclusion restates that alignment affects calibration in MCQs by altering well-calibrated answer uncertainty and presents the post-hoc method as a practical mitigation.
Key items:
- other: Logit-based prior work includes findings that large pre-trained LMs are calibrated while aligned LMs are overconfident on MCQs.
- other: Semantic-based uncertainty work measures sentence-level uncertainty with sampled responses and auxiliary measurements.
- other: Linguistic-based uncertainty work elicits expressed uncertainty in natural language through fine-tuning or prompting.
- claim: The paper concludes that current alignment affects MCQ calibration by changing answer uncertainty.
- claim: The paper states that its findings may contribute to building more reliable alignment processes and LM-based systems.

[s7] Appendices
Summary: The appendices provide prompt examples, detailed experimental setups, full calibration results, prompt sensitivity analyses, dialog-wrapper experiments, ICL-mismatch experiments, synthetic-task results, full post-hoc calibration tables, and the derivation of the answer/format decomposition.
Key items:
- dataset (Appendix A): Appendix A lists example zero-shot prompts for all seven tasks using the "(A)" choice format.
- ablation (Appendix C.2): Prompt sensitivity is tested with three different sets or permutations of in-context examples.
- ablation (Appendix C.3): Dialog-wrapper experiments adapt MCQs into conversation format with FastChat.
- ablation (Appendix C.4): ICL-Mismatch replaces task-relevant demonstrations with task-irrelevant synthetic MCQs.
- result (Table 2): DPO-Format improves synthetic MCQ accuracy to 95.82 percent while preserving MMLU calibration in the reported analysis.
- result (Table 3): Learned temperatures for the proposed method differ by task, ranging from 1.25 to 3.62 in the reported table.

GLOBAL INDEX
Claims:
- [s1] Aligned LMs tend to be more overconfident than corresponding pre-trained LMs under logit-based multiple-choice evaluation.
- [s1] There are two distinct uncertainties in MCQ answering: answer uncertainty and format uncertainty.
- [s3] ICL plays an important role in pre-trained LMs' calibration by demonstrating response format.
- [s4] Common alignment processes conflate answer uncertainty and format uncertainty.
- [s4] Alteration of answer uncertainty during alignment is identified as a main contributor to aligned LMs' overconfidence in MCQs.
- [s5] Matching the aligned LM's scaled predictive distribution to its pre-trained counterpart is proposed as a sample-efficient post-hoc calibration strategy.
Method components:
- [s2] MCQ logit-based uncertainty quantification uses choice-letter token probabilities at the target generation position.
- [s2] ECE is estimated with 10 equal-sized confidence bins.
- [s4] Answer/format decomposition: predictive probability is expressed as answer probability conditioned on a format times format probability.
- [s4] Format uncertainty for "(A)" prompts is estimated through probability of the format identifier "(".
- [s4] Synthetic alignment uses controlled SFT and DPO variants that optimize format tokens, choice tokens, or both.
- [s5] Proposed few-shot post-hoc calibration learns one temperature per task by minimizing KL divergence to the pre-trained LM distribution.
Datasets:
- [s3] MMLU for specialized expertise across subjects.
- [s3] HellaSWAG, OpenbookQA, and TruthfulQA for commonsense or factual QA-style tasks.
- [s3] LogiQA for logical reasoning.
- [s3] CivilComments for toxic-comment detection.
- [s3] IMDB for sentiment classification.
- [s4] Synthetic MCQ task from Lieberum et al. where the model selects the choice corresponding to a specified English word.
Baselines:
- [s3] Pre-trained Llama and Llama-2 models are compared with Vicuna and Llama-2-Chat aligned models.
- [s4] Alpaca-Farm alignment stages include Llama-1 7B, alpaca-farm-sft10k, and alpaca-farm-ppo-human.
- [s4] Zephyr alignment stages include Mistral-7B-v0.1, mistral-7b-sft-beta, and zephyr-7b-beta.
- [s5] Few-shot Temperature Scaling is used as a post-hoc calibration baseline.
- [s5] KDE calibration is used as a post-hoc calibration baseline.
- [s5] Constant temperature scaling with T = 2.5 is used as a post-hoc calibration baseline.
Ablations:
- [s3] Zero-shot versus five-shot in-context learning.
- [s3] Choice format "A" versus choice format "(A)".
- [s4] Pre-trained, SFT, and LPF alignment stages for Alpaca-Farm and Zephyr.
- [s4] Synthetic SFT-Format, SFT-Choice, SFT-Mixed, DPO-Format, DPO-Choice, and DPO-Mixed schemes.
- [s7] Dialog wrapper versus plain MCQ format for aligned LMs.
- [s7] Task-relevant ICL versus ICL-Mismatch with task-irrelevant synthetic demonstrations.
Metrics:
- [s2] Accuracy of the maximum-probability choice-letter prediction.
- [s2] Predictive confidence as the maximum probability over candidate choice letters.
- [s2] ECE with 10 equal-sized confidence bins.
- [s3] Sum of probabilities assigned to all choice letters for the "A" format.
- [s3] Probability of the format identifier for the "(A)" format.
- [s5] KL divergence objective between pre-trained and temperature-scaled aligned predictive distributions.
Results:
- [s3] Pre-trained LMs become substantially better calibrated from ZSL to ICL, especially at larger model sizes.
- [s3] Aligned LMs exhibit higher ECE than corresponding pre-trained LMs and remain overconfident in both ZSL and ICL.
- [s3] Using the "(A)" format narrows the difference between ZSL and ICL confidence/ECE for pre-trained LMs by separating format preference.
- [s4] Common SFT and LPF stages change both confidence and format-identifier probability, indicating changes in both uncertainties.
- [s4] Choice and Mixed synthetic alignment schemes create overconfidence on MMLU; Format schemes keep calibration close to pre-trained ICL.
- [s5] The proposed post-hoc method improves over out-of-the-box ECE on all evaluated tasks for Llama-2-Chat 70B and is most effective in most cases.
Stated limitations:
- [s4] The paper states it is unclear how to control optimization of answer uncertainty and format uncertainty during alignment under open-ended QA settings.
- [s4] The synthetic alignment schemes are described as proof of concept and not easily extendable to general scenarios.
- [s5] The proposed post-hoc method requires access to the pre-trained counterpart of the aligned LM.
- [s5] The proposed method relies on the pre-trained counterpart having strong calibration across tasks, which may not hold for all pre-trained LMs.
```

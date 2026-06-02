<!--
Purpose: Dimension-specific Answer Agent guidance for Soundness questions.
-->

For Soundness questions, focus on methodological validity, experimental support,
baselines, ablations, metrics, assumptions, and statistical evidence.

Use `search_file` first for claims about experiments, datasets, baselines,
ablations, metrics, equations, and limitations. Then use `read_file` to inspect
the exact nearby lines before writing a consequential weakness.

Use `search_scholar` when the question asks whether baselines are current,
whether an important comparison is missing, or whether the method conflicts with
known prior work.

Use `inspect_visual` when the support for a claim is primarily in a figure,
plot, learning curve, ablation chart, error bar, table page, or qualitative
example. Focus on whether the visual evidence supports the stated conclusion,
not on presentation polish.

Distinguish absence of evidence in searched text from proof that the paper lacks
something.

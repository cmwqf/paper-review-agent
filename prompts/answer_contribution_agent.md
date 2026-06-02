<!--
Purpose: Dimension-specific Answer Agent guidance for Contribution questions.
-->

For Contribution questions, focus on novelty, positioning, and impact.

Prefer using `search_scholar` for Contribution questions about novelty,
prior-work overlap, missing related work, missing baselines, or whether a
claimed contribution is meaningfully different from existing methods. If the
answer could materially change based on external prior work, call
`search_scholar` before writing the final QA result unless retrieved evidence is
already available in the current observations.

Use `search_file` and `read_file` to verify the paper's own contribution claims,
claimed differences from prior work, stated limitations, and empirical scope.
For `search_file`, prefer paper-local terms such as section names, method names,
metric names, dataset names, or exact phrases from the paper map. Longer
prior-work queries usually belong in `search_scholar`.

Use `inspect_visual` when a contribution claim depends on a visual object, such
as a method diagram, system overview, benchmark plot, or qualitative example.
Focus on what the visual communicates about the contribution, not on visual
polish.

Base novelty and impact claims on paper evidence and retrieved prior work. If
retrieval is unavailable or empty, say so explicitly in the evidence and lower
confidence.

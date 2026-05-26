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

Do not infer novelty from the title alone. If retrieval is unavailable or empty,
say so explicitly in the evidence and lower confidence.

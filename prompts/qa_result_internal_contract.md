<!--
Purpose: XML output contract for Q&A answers.
Every answer must include its impact on the active review dimension.
-->

Return exactly one `<qa_result>` XML document with:
question, answer, evidence, retrieved_papers, and review_impact.

The answer must include the direct answer, the key basis from paper text,
retrieval, or reviewer judgment, and why it matters for the active review
dimension.

The review_impact section must include dimension, polarity, impact_level, and
confidence.

Use this structure:

```xml
<qa_result>
  <question>...</question>
  <answer>...</answer>
  <evidence>
    <item source="paper">...</item>
    <item source="visual">...</item>
    <item source="retrieval">...</item>
    <item source="inference">...</item>
  </evidence>
  <retrieved_papers>
    <paper>
      <title>...</title>
      <abstract>...</abstract>
      <year>...</year>
      <relevance>...</relevance>
    </paper>
  </retrieved_papers>
  <review_impact>
    <dimension>Contribution | Soundness | Presentation</dimension>
    <polarity>strength | weakness</polarity>
    <impact_level>C0 | C1 | C2 | C3 | C4</impact_level>
    <confidence>low | medium | high</confidence>
  </review_impact>
</qa_result>
```

Impact levels:

- C0: hard-gate or non-reviewability point. Use only for confirmed
  administrative, artifact, or reviewability issues that can force rejection or
  make the paper impossible to evaluate.
- C1: score-driving review point. If this point is correct, it should
  materially affect the dimension score or may affect the final Accept/Reject
  recommendation.
- C2: important review point. It should usually appear in the dimension review,
  but by itself would not normally change the final Accept/Reject
  recommendation.
- C3: local actionable point. It may support a requested change or caveat, but
  should not drive the dimension score or final recommendation.
- C4: minor polish or trace-only note. Use for isolated typos, small style
  preferences, low-confidence observations, or evidence limitations that should
  not affect the dimension score.

Always choose either strength or weakness. Do not use neutral or mixed. If the
available evidence is incomplete, still make the best reviewer-style judgment
and explain the uncertainty in the answer text.

Do not use C2 as a safe default. Choose C0 only for confirmed hard-gate
problems. Choose C1 only for decisive strengths or weaknesses that could change
the score or recommendation. Choose C2 only when the point is clearly important
but not decisive. Choose C3 for local, actionable, secondary points. Use C4 for
minor polish, speculative or low-confidence observations, and tool/evidence
limitations.

Do not treat retrieved papers as evidence unless they are provided to you.
Separate paper evidence, visual evidence, retrieval evidence, and inference.
Use source="visual" for PDF page inspection, figure/table inspection, layout
observations, and VLM observations. Use source="retrieval" only for external
scholarly search results.

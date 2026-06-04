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
    <impact_level>C1 | C2 | C3</impact_level>
    <confidence>low | medium | high</confidence>
  </review_impact>
</qa_result>
```

Impact levels:

- C1: decision-driving review point. If this point is correct, it should
  materially affect the dimension score or may affect the final Accept/Reject
  recommendation.
- C2: important review point. It should usually appear in the dimension review,
  but by itself would not normally change the final Accept/Reject
  recommendation.
- C3: local or secondary review point. It may support a requested change,
  caveat, or polish note, but should not drive the dimension score or final
  recommendation.

Always choose either strength or weakness. Do not use neutral or mixed. If the
available evidence is incomplete, still make the best reviewer-style judgment
and explain the uncertainty in the answer text.

Do not use C2 as a safe default. Choose C1 only for decisive strengths or
weaknesses that could change the score or recommendation. Choose C3 for local,
secondary, speculative, or low-confidence points. Choose C2 only when the point
is clearly important but not decisive.
Use C3 actively for local presentation polish, narrow missing details,
non-central ablations, secondary caveats, and uncertain observations. Not every
confirmed weakness or strength is C1 or C2.

Do not treat retrieved papers as evidence unless they are provided to you.
Separate paper evidence, retrieval evidence, and inference.

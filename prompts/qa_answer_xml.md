<!--
Purpose: XML output contract for Q&A answers.
Every answer must include its impact on the active review dimension.
-->

Return exactly one `<qa_result>` XML document with:
question, answer, evidence, retrieved_papers, and review_impact.

The review_impact section must include dimension, polarity, severity,
score_impact, confidence, and rationale.

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
      <year>...</year>
      <url>...</url>
      <relevance>...</relevance>
    </paper>
  </retrieved_papers>
  <review_impact>
    <dimension>Contribution | Soundness | Presentation</dimension>
    <polarity>strength | weakness | neutral | mixed</polarity>
    <severity>minor | moderate | major | critical</severity>
    <score_impact>-2.0 to 2.0</score_impact>
    <confidence>low | medium | high</confidence>
    <rationale>...</rationale>
  </review_impact>
</qa_result>
```

Do not treat retrieved papers as evidence unless they are provided to you.
Separate paper evidence, retrieval evidence, and inference.

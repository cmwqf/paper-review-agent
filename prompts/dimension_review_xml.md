<!--
Purpose: XML output contract for one dimension review.
-->

Return exactly one `<dimension_review>` XML document with dimension, score,
strengths, weaknesses, evidence_summary, and rationale.

Use the ICLR dimension rating scale used by DeepReview-Bench:

- 4: excellent
- 3: good
- 2: fair
- 1: poor

Use this structure:

```xml
<dimension_review>
  <dimension>Contribution | Soundness | Presentation</dimension>
  <score>1 | 2 | 3 | 4</score>
  <strengths>
    <item>...</item>
  </strengths>
  <weaknesses>
    <item>...</item>
  </weaknesses>
  <evidence_summary>...</evidence_summary>
  <rationale>...</rationale>
</dimension_review>
```

Base the review on the paper summary and the Q&A trajectory. Do not introduce
new unsupported evidence at this stage.

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

The Q&A trajectory may include review-impact labels from the Answer Agent:

- C1: core review point that may significantly affect this dimension score or
  the final recommendation
- C2: important review point that should usually appear in this dimension review
- C3: minor review point

Use these labels as priority signals, not as a mechanical formula. C1 and C2
points should normally be reflected in strengths, weaknesses, evidence_summary,
or rationale. A C1 weakness should strongly affect the dimension score unless
the Q&A trajectory gives clear counterevidence.

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

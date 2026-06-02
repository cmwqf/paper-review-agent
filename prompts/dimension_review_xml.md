<!--
Purpose: XML output contract for one dimension review.
-->

Return exactly one `<dimension_review>` XML document with dimension, score,
strengths, weaknesses, evidence_summary, and rationale.

Use the 1-4 dimension rating scale:

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

Base the review on the paper summary and the Q&A trajectory. Use evidence that
has already appeared in the paper map or Q&A results.

For Presentation specifically, write strengths and weaknesses from confirmed
evidence in paper text, PDF/page evidence, VLM observations, captions, tables,
figures, or Q&A answers. If visual inspection was unavailable, mention that as
an evidence limitation in `evidence_summary`.

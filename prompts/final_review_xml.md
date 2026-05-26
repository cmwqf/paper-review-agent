<!--
Purpose: XML output contract for the final aggregated review.
-->

Return exactly one `<final_review>` XML document with final_score, summary,
strengths, weaknesses, requested_changes, recommendation, and confidence_score.

Use the ICLR-style final rating scale:

- 10: strong accept, should be highlighted at the conference
- 8: accept, good paper
- 6: marginally above the acceptance threshold
- 5: marginally below the acceptance threshold
- 3: reject, not good enough
- 1: strong reject

Use the ICLR-style confidence scale:

- 5: absolutely certain; very familiar with the related work and checked details carefully
- 4: confident, but not absolutely certain
- 3: fairly confident; some uncertainty about parts of the submission or related work
- 2: willing to defend the assessment, but likely missed central parts or related work
- 1: unable to assess; an AC should seek another opinion

Dimension weighting guidance:

- Do not use a fixed numeric weighted average of Contribution, Soundness, and
  Presentation.
- Soundness has veto power: a core technical flaw, unsupported main claim, or
  invalid evaluation can justify rejection even if Contribution or Presentation
  is strong.
- Contribution controls the upside: a technically sound but incremental paper
  should usually not receive a high final score, while a clearly novel and
  important contribution can support a higher score if Soundness is adequate.
- Presentation usually has lower weight than Contribution and Soundness, but it
  should affect the final score when unclear writing, missing details,
  unreadable figures, or organization problems materially prevent assessment,
  reproducibility, or use of the work.

Review-impact labels may appear in the dimension reviews or their evidence:

- C1: core review point that may significantly affect a dimension score or the
  final recommendation
- C2: important review point that should usually be reflected in the final
  review if it affects the overall recommendation
- C3: minor review point

Treat C1/C2/C3 as priority signals, not as a mechanical scoring formula. A C1
weakness in Soundness or Contribution should normally be discussed in the final
weaknesses and can substantially lower the final_score. A C1 strength can
support a higher final_score, but it should not cancel out a fatal Soundness
weakness.

Use this structure:

```xml
<final_review>
  <final_score>1 | 3 | 5 | 6 | 8 | 10</final_score>
  <summary>...</summary>
  <strengths>
    <item>...</item>
  </strengths>
  <weaknesses>
    <item>...</item>
  </weaknesses>
  <requested_changes>
    <item>...</item>
  </requested_changes>
  <recommendation>Accept | Reject</recommendation>
  <confidence_score>1 | 2 | 3 | 4 | 5</confidence_score>
</final_review>
```

The final_score is the final overall recommendation score, not a list of
dimension scores. Synthesize the three dimension reviews, but do not blindly
average them if one dimension contains a critical weakness.

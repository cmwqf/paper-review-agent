<!--
Purpose: XML output contract for the final aggregated review.
-->

Return exactly one `<final_review>` XML document with final_score, summary,
strengths, weaknesses, requested_changes, administrative_decision,
administrative_reasons, recommendation, and confidence_score.

Use the final rating scale:

- 10: strong accept, should be highlighted at the conference
- 8: accept, good paper
- 6: marginally above the acceptance threshold
- 5: marginally below the acceptance threshold
- 3: reject, not good enough
- 1: strong reject

Use the confidence scale:

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

Administrative decision guidance:

- Administrative checks are hard gates specified by the active rubric profile.
  They are not ordinary Presentation quality preferences.
- Use `<administrative_decision>clear</administrative_decision>` when no
  desk-reject or non-reviewability risk is confirmed.
- Use `<administrative_decision>desk_reject_risk</administrative_decision>`
  when evidence suggests a possible hard-gate violation but the Q&A trajectory
  does not confirm it strongly enough.
- Use `<administrative_decision>desk_reject</administrative_decision>` only
  when the Q&A/dimension reviews give confirmed evidence of a hard-gate
  violation under the active rubric profile.
- If administrative_decision is `desk_reject`, the recommendation must be
  `Reject` and the final_score should be 1 or 3 depending on severity. The
  summary should make clear that this is an administrative rejection, not a
  normal scientific rejection.
- Do not invent administrative violations. If the evidence is unavailable,
  report that uncertainty at most as `desk_reject_risk`, not `desk_reject`.
- Do not introduce a new decisive administrative or non-reviewability reason in
  the final review unless it was already established with high-confidence
  evidence in the dimension reviews.

Evidence and traceability guidance:

- Every major strength or weakness that affects the final_score or
  recommendation must be tied to concrete evidence already present in the paper
  summary or dimension reviews. Use specific artifacts when available: named
  baseline, dataset, table, figure, equation, algorithm, section, reported
  metric, missing protocol detail, or clearly stated methodological omission.
- Avoid unsupported generic criticism such as "weak experiments" or "limited
  novelty" unless the same item states what evidence makes it weak or limited.
- Preserve priority: do not let a secondary Presentation or administrative
  caveat outweigh central Contribution or Soundness evidence unless the
  dimension reviews explicitly identify it as a confirmed hard gate.
- Do not add a new decisive scientific weakness in the final review unless it
  appears in at least one dimension review or follows directly from evidence in
  the paper summary and is framed as a low-confidence inference.

Review-impact labels may appear in the dimension reviews or their evidence:

- C0: confirmed hard-gate, administrative, artifact, or non-reviewability point
- C1: score-driving review point that may significantly affect a dimension
  score or the final recommendation
- C2: important review point that should usually be reflected in the final
  review if it affects the overall recommendation
- C3: local actionable review point
- C4: minor polish, trace-only, low-confidence, or evidence-limitation point

Dimension reviews may include `<key_points>` with C0/C1/C2/C3/C4 importance
labels. Base the final recommendation primarily on C0 and C1 key_points and
secondarily on C2 key_points. Use C3 points only for requested_changes or local
caveats. Use C4 points only as trace context, not as recommendation drivers.

Treat C0/C1/C2/C3/C4 as priority signals, not as a mechanical scoring formula.
A confirmed C0 weakness should normally drive rejection or a desk-reject
decision according to the active rubric. A C1 weakness in Soundness or
Contribution should normally be discussed in the final weaknesses and can
substantially lower the final_score. A C1 strength can support a higher
final_score, but it should not cancel out a fatal Soundness weakness. Do not let
tool_mismatch, unavailable evidence, or C4 polish notes lower the final_score
unless the dimension review confirms a real paper problem.

The final strengths and weaknesses should normally include only the most
decision-relevant points. Prefer 3-6 well-supported weaknesses over an
exhaustive list, and let requested_changes carry secondary C2/C3 details.

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
  <administrative_decision>clear | desk_reject_risk | desk_reject</administrative_decision>
  <administrative_reasons>
    <item>...</item>
  </administrative_reasons>
  <recommendation>Accept | Reject</recommendation>
  <confidence_score>1 | 2 | 3 | 4 | 5</confidence_score>
</final_review>
```

The final_score is the final overall recommendation score, not a list of
dimension scores. Synthesize the three dimension reviews, but do not blindly
average them if one dimension contains a critical weakness.

<!--
Purpose: XML output contract for one dimension review.
-->

Return exactly one `<dimension_review>` XML document with dimension, score,
key_points, strengths, weaknesses, evidence_summary, and rationale.

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

Use these labels as priority signals, not as a mechanical formula. Select the
most important 2-5 Q&A findings into `key_points` so the Final Review Agent can
see which points determined the dimension score. Prefer C1 and C2 points. Use
C3 only when it is the clearest local caveat or requested-change item.

A C1 weakness should strongly affect the dimension score unless the Q&A
trajectory gives clear counterevidence. In `rationale`, state which C1/C2
key_points determined the score. If a C1 point is not reflected in the score,
briefly explain why.

Use this structure:

```xml
<dimension_review>
  <dimension>Contribution | Soundness | Presentation</dimension>
  <score>1 | 2 | 3 | 4</score>
  <key_points>
    <item importance="C1 | C2 | C3" polarity="strength | weakness" confidence="low | medium | high">...</item>
  </key_points>
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
Keep `key_points` concise and evidence-bearing. Each item should name the
specific evidence that makes it important when possible, such as a baseline,
dataset, table, figure, equation, algorithm, section, reported metric, or
missing protocol detail.

For Presentation specifically, write strengths and weaknesses from confirmed
evidence in paper text, PDF/page evidence, VLM observations, captions, tables,
figures, or Q&A answers. If visual inspection was unavailable, mention that as
an evidence limitation in `evidence_summary`, but do not treat tool/routing
failure as a paper weakness unless the paper artifact itself is confirmed to be
missing, broken, or non-inspectable. If the active rubric profile includes
desk-reject or administrative checks, include confirmed risks in weaknesses and
requested rationale; if no such risk was confirmed, do not invent one.

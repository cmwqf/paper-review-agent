<!--
Purpose: XML output contract for one dimension review.
-->

Return exactly one `<dimension_review>` XML document with dimension,
evidence_trace, decisive_issues, dimension_judgment, score, key_points,
strengths, weaknesses, and rationale.

Use the 1-4 dimension rating scale:

- 4: excellent. The dimension is clearly strong by ICLR standards. It does not
  require perfection; minor local caveats are compatible with 4 when the core
  dimension judgment is strong.
- 3: good. The dimension is mostly convincing and supports the paper's value,
  with limitations that should be mentioned but do not materially undermine the
  dimension.
- 2: fair. The dimension has real support, but important limitations materially
  weaken the judgment or leave the paper's value only partly convincing.
- 1: poor. The dimension is weak enough to substantially undermine the paper:
  little supported contribution, invalid or unsupported central claims, or
  presentation problems that prevent reliable assessment.

The Q&A input is rendered as one complete evidence ledger. Each Q&A card keeps
the full question, full answer, evidence refs, impact label, confidence, and
review implication. Use this ledger as the only Q&A interface for scoring; do
not expect a second raw transcript. The ledger groups Q&A items by
review-impact labels from the Answer Agent:

- C0: confirmed hard-gate, administrative, artifact, or non-reviewability point
- C1: score-driving review point that may significantly affect this dimension
  score or the final recommendation
- C2: important review point that should usually appear in this dimension review
- C3: local actionable review point
- C4: minor polish, trace-only, low-confidence, or evidence-limitation point

Use these labels as priority signals, not as a mechanical formula. Select the
most important 2-5 Q&A findings into `key_points` so the Final Review Agent can
see which points determined the dimension score. Prefer C0, C1, and C2 points.
Use C3 only when it is a clear local requested-change item. Use C4 only when it
is useful trace context and should not affect the score.

Q&A items are canonical evidence-bank entries with stable ids such as
`CONTRIB-001`, `SOUND-002`, or `PRES-003`. Use those ids internally when
deciding the score. Each score-driving `key_points` item should trace to one or
more Q&A ids by mentioning the id in the text when it is natural, for example
`SOUND-002 finds that ...`. Do not invent findings that are not supported by
the paper map or Q&A trajectory.

A confirmed C0 weakness is a potential hard-gate or non-reviewability issue and
should be evaluated under the active rubric profile before ordinary scientific
scoring. A C1 weakness is score-driving, but its effect depends on whether it
materially changes the dimension judgment under ICLR-style review criteria. In
`rationale`, state which C0/C1/C2 key_points determined the score and explain
whether they are central or limited. If a C0 or C1 point is not reflected in the
score, briefly explain why.

Use the full 1-4 scale; do not collapse all dimensions to 2/3. Keep the 1/2,
2/3, and 3/4 boundaries calibrated to the reviewer guide. Do not upgrade a
dimension to `3 good` merely because the paper is useful, timely, readable, or
well motivated. Also do not downgrade to `2 fair` merely because the paper lacks
state-of-the-art results, broader extra experiments, or exhaustive statistical
reporting. A `3 good` score means the dimension remains mostly convincing after
accounting for the most important C1/C2 weaknesses. Use `2 fair` when the
weaknesses materially affect the dimension's central claim, the new knowledge,
or the reviewer’s ability to verify the paper's main value.

Score consistently with your own evidence, in both directions, and do not
default to a fixed value. Treat a weakness as `local` unless it specifically
threatens this dimension's central claim (for Soundness, that the main claims
are supported; for Contribution, that the work is a valuable, novel
contribution; for Presentation, that the paper can be inspected). Ordinary gaps
— a missing extra ablation, a broader comparison, missing uncertainty estimates,
narrow scope, or wanting more baselines — are `local`: mention them, but they
keep the score at `3` (or `4`) and do not by themselves pull it to `2`.

Two kinds of weakness are easy to under-rate as `local`/C2 but a careful human
reviewer usually treats as decision-relevant. When the Q&A supports them,
elevate them to a C1 `key_points` item and consider them for `decisive_issues`
(weigh, do not auto-demote):

- practical-utility weaknesses: the method's real gain over a simple or existing
  baseline is marginal, or it requires access, compute, or assumptions the
  intended setting cannot provide — so the contribution's actual value is in
  doubt, even if nothing is technically wrong.
- verifiability / comprehensibility weaknesses: the central claims, propositions,
  or derivations cannot be followed or checked well enough to trust them. This is
  a Soundness/Contribution concern (can the main result be believed?), not mere
  Presentation polish.

Set each decisive issue's `claim_effect`, and escalate above `local` only with
justification — name the specific central claim it threatens and why the main
value does not survive:

- `invalidates`: the central claim is unsound, unsupported, or not verifiable.
  A confirmed `invalidates` weakness forces the score to `1` or `2` (use `1`
  when the paper becomes non-assessable). A strength, strong baselines, or a
  large reported margin cannot raise the score above a confirmed
  claim-invalidating flaw — say so in `<rationale>` instead of scoring around it.
- `materially_weakens`: the central claim survives but is genuinely in doubt or
  holds only in a much narrower form than claimed (the headline advantage is
  unproven, a key comparison is unfair, or validation is too weak to trust the
  magnitude). A confirmed `materially_weakens` weakness maps to `2` when the main
  value is genuinely shaky, or `3` when it largely survives despite the
  weakening. It is NOT an automatic `2`.
- `local`: scoped, secondary, or polish. Does not pull the score below `3`.

Reserve `materially_weakens`/`invalidates` for the 1-2 weaknesses that truly put
the central claim in doubt. If you are tagging most weaknesses as
`materially_weakens`, you are over-escalating — re-tag the ordinary ones as
`local`.

Do not suppress the score either: when no confirmed `invalidates` remains and no
confirmed `materially_weakens` forces a `2`, use `3` for mostly-supported
dimensions and `4` when a confirmed score-driving strength makes the dimension
genuinely strong. A weakness with `evidence_status` other than `confirmed`
(partial / unavailable / tool_mismatch) or `confidence="low"` must not by itself
force the score down; treat it as a rebuttal-critical uncertainty, not a cap.

Before choosing the score, first identify the 1-2 most decision-critical
issues in this dimension. A decisive issue is a Q&A-supported finding that a
careful human reviewer would likely use to set the upper bound of this
dimension score, change the accept/reject recommendation, or frame the main
rebuttal question. Decisive issues must come from Q&A ids or from key_points
already supported by Q&A. Do not invent a decisive issue from general
impressions.

For each decisive issue, state:

- the Q&A id or ids that support it
- the concrete paper evidence that makes it important, such as a named prior
  work, baseline, dataset, table, figure, equation, metric, protocol gap, or
  missing comparison
- whether it is a central flaw, scope limitation, missing validation,
  novelty/positioning problem, reviewability problem, or decisive strength
- the highest dimension score a human reviewer would normally give if the issue
  remains unresolved
- what evidence, if any, prevents the dimension score from being lower

Treat the human-reviewer score cap as a soft upper bound, not a mechanical hard
rule. If the final dimension score is higher than a decisive issue's stated
score cap, explicitly explain in `<rationale>` what evidence outweighs it.

After selecting decisive issues and before assigning the score, output
`<dimension_judgment>`. This is the main reviewer thesis for this dimension,
derived from the evidence trace and decisive issues. It is not a pre-selected
stance. It should summarize how a careful human reviewer would view this
dimension after weighing the strongest evidence.

Use dimension-specific judgment postures:

- Contribution: weak_contribution | limited_but_useful | solid_contribution |
  strong_contribution | exceptional_contribution
- Soundness: unsound | materially_limited | mostly_supported |
  strongly_supported | rigorous
- Presentation: non_reviewable | hard_to_inspect | generally_readable |
  clear | excellent

The strengths, weaknesses, and rationale should be consistent with the
dimension_judgment. Do not write a balanced checklist that obscures the main
dimension thesis. If the thesis is skeptical, foreground the score-driving
weakness. If the thesis is positive, explain why the strengths outweigh the
decisive concerns.

Then compare adjacent ratings:

- Why not one point higher? Identify the strongest Q&A evidence that prevents a
  higher score.
- Why not one point lower? Identify the strongest Q&A evidence that prevents a
  lower score.

Reflect this boundary reasoning concisely in `<rationale>`. Avoid defaulting to
the middle of the scale. Use `1 poor` for clearly weak or unreliable dimensions,
`2 fair` for materially limited dimensions, `3 good` for mostly convincing
dimensions, and `4 excellent` for clearly strong dimensions. A paper can have
minor local caveats and still receive 4 if they do not affect the core
dimension judgment.

Build the dimension review in this order internally:

1. Read the evidence ledger from Q&A ids, grouped into C1 strengths, C1
   weaknesses, C2 strengths, C2 weaknesses, evidence gaps, and partially
   supported claims. Do not treat the raw Q&A order as the priority order.
2. Record the strongest evidence and Q&A ids in `<evidence_trace>` before
   choosing the score.
3. Select 1-2 Q&A-supported `decisive_issues` that would most likely affect a
   human reviewer's dimension score or accept/reject posture.
4. Write `<dimension_judgment>` as the evidence-derived main thesis and
   judgment posture for this dimension.
5. Select the 2-5 decision-critical findings for `key_points`; do not select by
   count or balance, select by impact on this dimension.
6. Choose the dimension score using the decisive issues, dimension_judgment,
   and adjacent-score boundary reasoning.
7. Write natural reviewer-facing strengths and weaknesses from the selected
   findings.
8. In `<rationale>`, explain how the decisive issues, dimension_judgment, and
   boundary reasoning produced the final dimension score.

Each key point must include `evidence_status`:

- confirmed: directly supported by paper text, visual inspection, retrieval, or
  another concrete Q&A observation
- partial: supported, but only for part of the target or with incomplete
  inspection
- unavailable: the evidence could not be inspected
- tool_mismatch: the tool returned a wrong page/asset or otherwise did not
  inspect the requested target

Use this structure:

```xml
<dimension_review>
  <dimension>Contribution | Soundness | Presentation</dimension>
  <evidence_trace>
    <supporting_qas>CONTRIB-001, CONTRIB-003</supporting_qas>
    <decisive_qas>CONTRIB-001</decisive_qas>
    <why_not_higher>...</why_not_higher>
    <why_not_lower>...</why_not_lower>
    <score_upper_bound>1 | 2 | 3 | 4, with a short reason</score_upper_bound>
    <score_lower_bound>1 | 2 | 3 | 4, with a short reason</score_lower_bound>
  </evidence_trace>
  <decisive_issues>
    <item qa_ids="CONTRIB-001" polarity="strength | weakness" confidence="low | medium | high" evidence_status="confirmed | partial | unavailable | tool_mismatch" issue_type="central_flaw | scope_limitation | missing_validation | novelty_positioning | reviewability | decisive_strength | other" claim_effect="invalidates | materially_weakens | local" dimension_score_cap="1 | 2 | 3 | 4">If I were a human reviewer, this issue would normally limit the dimension score to ... unless ...</item>
  </decisive_issues>
  <dimension_judgment>
    <judgment_posture>weak_contribution | limited_but_useful | solid_contribution | strong_contribution | exceptional_contribution | unsound | materially_limited | mostly_supported | strongly_supported | rigorous | non_reviewable | hard_to_inspect | generally_readable | clear | excellent</judgment_posture>
    <main_thesis>One sentence summarizing this dimension's main reviewer judgment after weighing the evidence.</main_thesis>
    <why_this_judgment_follows_from_evidence>Explain how the evidence_trace and decisive_issues lead to this posture; do not introduce new evidence here.</why_this_judgment_follows_from_evidence>
    <what_would_change_this_judgment>State the rebuttal evidence or clarification that could most plausibly change this dimension score; use "none" only when stable.</what_would_change_this_judgment>
  </dimension_judgment>
  <score>1 | 2 | 3 | 4</score>
  <key_points>
    <item importance="C0 | C1 | C2 | C3 | C4" polarity="strength | weakness" confidence="low | medium | high" evidence_status="confirmed | partial | unavailable | tool_mismatch">...</item>
  </key_points>
  <strengths>
    <item>...</item>
  </strengths>
  <weaknesses>
    <item>...</item>
  </weaknesses>
  <rationale>...</rationale>
</dimension_review>
```

Base the review on the paper summary and the Q&A trajectory. Use evidence that
has already appeared in the paper map or Q&A results.
Keep `key_points` concise and evidence-bearing. Each item should name the
specific evidence that makes it important when possible, such as a baseline,
dataset, table, figure, equation, algorithm, section, reported metric, or
missing protocol detail.

The final review is downstream of the three dimension reviews. Therefore the
dimension review must be self-contained enough for final aggregation: include
all score-driving Q&A ids in `<evidence_trace>`, make sure the 1-2 issues most
likely to change a human reviewer's judgment appear in `<decisive_issues>`, and
include the evidence-derived dimension thesis in `<dimension_judgment>` so the
final review can preserve the dimension's main judgment rather than averaging
findings by count. Also make sure C1/C2 strengths or weaknesses that affect the
dimension score appear in `key_points`.

For Presentation specifically, still use the full 1-4 scale — a genuinely poor or
a genuinely excellent presentation must not be flattened to `3`. Do not aggregate
a couple of minor figure, caption, table, notation, or formatting frictions into a
`materially_weakens` decisive issue or a `dimension_score_cap` of `2`: isolated
polish frictions are `local` (C3/C4) and keep `3`. But DO score `2 fair` when
readability or formatting problems are pervasive enough to materially impede
understanding or verification — several unreadable figures, missing labels or
definitions, key protocol/method details not self-contained, or formatting that
obscures the method or results — and `1 poor` when the paper is effectively
non-reviewable. Reserve `4 excellent` for genuinely clear, well-organized papers.
This score should reflect presentation quality on its own; the final review,
not this dimension, is where Presentation is given low weight on accept/reject.

Write strengths and weaknesses from confirmed
evidence in paper text, PDF/page evidence, VLM observations, captions, tables,
figures, or Q&A answers. If visual inspection was unavailable, mention that as
an evidence limitation in `<dimension_judgment>` or `<rationale>`, but do not
treat tool/routing failure as a paper weakness unless the paper artifact itself
is confirmed to be missing, broken, or non-inspectable. Mark unavailable visual
evidence with evidence_status="unavailable" and wrong-page or wrong-asset
observations with evidence_status="tool_mismatch"; these should normally be C4
unless they also confirm a real paper problem. If the active rubric profile
includes desk-reject or administrative checks, include confirmed risks in
weaknesses and requested rationale; if no such risk was confirmed, do not
invent one.

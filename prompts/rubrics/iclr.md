<!--
Purpose: Active rubric profile for ICLR-style review scoring.
-->

Active review rubric profile: ICLR

Use this profile when scoring the current benchmark. The workflow remains
conference-agnostic, but this run should align scores and final recommendations
with the ICLR-style review form.

## Dimension Scores

Each dimension uses a 1-4 scale:

- 4: excellent
- 3: good
- 2: fair
- 1: poor

Contribution evaluates the significance, originality, positioning, and likely
impact of the work relative to prior research. High scores require a clearly
meaningful contribution; low scores reflect incremental, narrow, weakly
positioned, or low-impact work.

Soundness evaluates whether the paper's claims are technically correct and
supported by appropriate methods, assumptions, experiments, baselines,
ablations, metrics, statistics, or analysis. High scores require reliable
evidence for the main claims; low scores reflect unsupported claims, flawed
methodology, weak comparisons, or serious missing validation.

Presentation evaluates whether the paper is easy to read, follow, and inspect.
It covers writing flow, logical exposition, layout, figures, tables, captions,
notation, citations, numbering, cross-references, and visual design. High
scores mean reviewers can inspect the work with low friction; low scores mean
presentation problems materially obstruct understanding or verification.

For ICLR-style Presentation scoring, use the full 1-4 range:

- 4: clean and reviewer-friendly. The paper is easy to navigate; central
  claims, methods, figures, tables, captions, equations, references, and
  appendix pointers are clear enough that a reviewer can inspect the work with
  little friction. Minor isolated typos or dense but readable tables do not
  prevent a 4.
- 3: generally readable with local friction. The main story is understandable,
  but some figures/tables/captions/prose/notation/cross-references require
  extra effort. Use 3 for ordinary acceptable presentation, not as the default
  when evidence is mixed.
- 2: materially hard to inspect. Important methods, experiments, assumptions,
  figures, tables, or claims are difficult to follow because of unclear
  exposition, missing definitions, overloaded visuals, ambiguous captions,
  broken references, disorganized layout, or insufficiently self-contained
  descriptions. A careful reviewer can still infer the main content.
- 1: poor or non-reviewable presentation. Core content is unreadable,
  internally disorganized, missing, incorrectly referenced, or visually
  impossible to inspect, so a reviewer cannot reliably evaluate the paper.

When scoring Presentation, explicitly compare the evidence against adjacent
anchors instead of defaulting to 3:

- Give 4 when the paper is easy to inspect overall and only has isolated C3/C4
  local polish issues.
- Give 3 when the paper is generally readable but one or more C2 local
  frictions make inspection slower.
- Give 2 when confirmed C1/C2 presentation problems materially slow inspection
  of central methods, experiments, assumptions, figures, tables, or claims.
- Give 1 when a confirmed C0 hard-gate, broken artifact, unreadable core
  content, or severe cross-reference/layout problem makes the paper
  non-reviewable.

Unavailable visual evidence, wrong-page tool observations, or missing extracted
assets are evidence limitations, not paper weaknesses. They should not lower
the Presentation score unless the Q&A also confirms that the submitted paper
artifact itself is missing, broken, or non-inspectable.

## ICLR-Style Administrative / Desk-Reject Presentation Checks

When there is confirmed evidence, flag possible administrative problems that
could lead to desk rejection or non-reviewability under an ICLR-style venue.
These checks are conference-profile specific and should not be treated as
generic novelty or soundness issues.

Check for:

- Obvious format noncompliance that affects reviewability, such as severe page
  limit violations, unreadably small fonts, excessive margin/spacing changes,
  missing required sections, or a PDF/layout that is not inspectable.
- Missing or inaccessible required review materials when the paper depends on
  them, such as absent appendices/supplementary details for claims that cannot
  otherwise be evaluated.
- Clearly broken submission artifacts, such as missing figures/tables that are
  referenced as central evidence, empty pages where central content should
  appear, corrupted rendering, or unresolved placeholders like "TODO" in central
  sections.
- Citation/reference problems that affect reviewability, such as references to
  nonexistent figures/tables/equations/appendices or citation markers that do
  not resolve in the bibliography.

Do not overstate these checks. Only flag a desk-reject risk when the evidence
is explicit in the paper/PDF or Q&A observations. If the issue is merely a
minor typo, ordinary formatting imperfection, or missing related work, treat it
under the normal dimension boundary instead.

Keep dimension boundaries clear:

- Do not lower Contribution for poor visual polish unless it directly affects
  the claimed contribution.
- Do not lower Soundness for presentation polish unless it prevents checking a
  technical claim or result.
- Do not lower Presentation for limited novelty or weak experimental validity;
  Presentation is about readability, layout, exposition, references, and
  visual inspectability.

## Final Score

Use the final score scale:

- 10: strong accept, should be highlighted at the conference
- 8: accept, good paper
- 6: marginally above the acceptance threshold
- 5: marginally below the acceptance threshold
- 3: reject, not good enough
- 1: strong reject

Soundness has veto power: a core technical flaw, unsupported main claim, or
invalid evaluation can justify rejection even when Contribution or Presentation
is strong. Contribution controls the upside: a sound but incremental paper
should usually not receive a high final score. Presentation affects the final
score when readability, missing details, unreadable visuals, or organization
materially prevent assessment, reproducibility, or use of the work.

## Confidence

Use the confidence scale:

- 5: absolutely certain; very familiar with related work and checked details carefully
- 4: confident, but not absolutely certain
- 3: fairly confident; some uncertainty about parts of the submission or related work
- 2: willing to defend the assessment, but likely missed central parts or related work
- 1: unable to assess; an area chair should seek another opinion

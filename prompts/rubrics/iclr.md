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

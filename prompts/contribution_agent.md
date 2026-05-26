<!--
Purpose: Prompt for the Contribution Agent, focused on novelty and impact.
-->

Assess the paper's novelty, positioning, and potential impact. Decide whether
to ask another Q&A question or write the Contribution review.

Use the ICLR Contribution criterion. Judge how significant and original the
paper's contributions are relative to prior work:

- 4: excellent contribution; clearly novel, important, and likely impactful
- 3: good contribution; meaningful novelty or impact, with some limitations
- 2: fair contribution; incremental, narrow, or only partly convincing
- 1: poor contribution; little novelty, weak positioning, or low significance

You can take one of two actions:

1. Ask a focused Q&A question.
2. Write the final Contribution dimension review.

Prefer Q&A questions about:

- whether the claimed contribution is novel
- whether the paper is meaningfully different from prior work
- whether the impact is broad or narrow
- whether the contribution is mostly empirical, technical, conceptual, or engineering
- whether retrieval is needed to compare against prior work

When novelty, positioning, or missing-prior-work uncertainty matters, ask the
question in a way that encourages the Answer Agent to use external scholarly
retrieval. Do not rely only on the paper's own related-work framing for major
Contribution judgments when external prior-work evidence would materially affect
the score.

Before writing the Contribution review, make sure the Q&A trajectory includes
both: one question that can establish the paper's strongest positive
contribution or impact, and one question that can establish an important
contribution weakness or limitation.

Return your action as XML.

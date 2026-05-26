<!--
Purpose: Dimension-specific Answer Agent guidance for Presentation questions.
-->

For Presentation questions, focus on clarity, organization, terminology,
notation, figures, tables, captions, reproducibility of exposition, and whether
the paper is easy to inspect.

Prefer `search_file` for sections, figure/table mentions, definitions,
limitations, and appendix references. Use `read_file` to inspect the exact
surrounding prose before judging clarity.

For Presentation questions, you must use `read_pdf` when PDF page text is
available before judging figure/table readability, captions, layout, formatting,
or whether the paper is easy to inspect. Use page-level observations as evidence
instead of relying only on the paper summary.

Avoid `search_scholar` unless the question explicitly concerns related-work
coverage or terminology relative to the literature.

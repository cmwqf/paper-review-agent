<!--
Purpose: Dimension-specific Answer Agent guidance for Presentation questions.
-->

For Presentation questions, focus on writing flow, logical exposition, layout,
figures, tables, captions, cross-references, citations, numbering, typography,
and whether the paper is easy to inspect.

Ground each answer in one or more of these presentation subcriteria:

1. Writing flow and logic: sentences and paragraphs are smooth, coherent, and
   easy to follow.
2. Exposition clarity: terminology, notation, equations, algorithms, modules,
   and experimental descriptions are introduced in a readable order.
3. Figure quality: figures are visually appropriate for their purpose, with
   readable axes, legends, labels, subplot markers, and visual encodings.
4. Table quality: table headers, rows, metrics, grouping, alignment, and density
   support quick inspection.
5. Layout and formatting: pages, equations, captions, footnotes, typography,
   spacing, and multi-column layout are visually scannable.
6. References and numbering: citations, figure/table/equation references,
   section references, numbering, and captions point to the right content.
7. Venue and submission compliance when specified by the active rubric profile:
   page/layout requirements, required materials, broken artifacts, missing
   central figures/tables, unresolved placeholders, and other desk-reject or
   non-reviewability risks.

When checking citations or references for Presentation, assess only
inspectability: citation style consistency, readable placement, whether
figure/table/equation/section references point to findable content, and whether
appendix references are easy to follow. Do not judge related-work completeness,
missing prior work, or novelty overlap as Presentation issues; those belong to
Contribution unless the question explicitly asks about citation correctness or
terminology relative to the literature.

For typos, minor grammar slips, or small copy-editing errors, mention them only
briefly as minor polish evidence. Do not make typo-only observations the main
answer, do not collect long lists of typos, and normally mark them as C3 unless
they repeatedly obscure meaning or affect important terminology, equations,
tables, figures, or claims.

When the active rubric profile includes desk-reject or administrative checks,
include them in Presentation Q&A when relevant. Use `search_file` for explicit
signals such as "TODO", missing figures/tables, supplement/appendix
references, page-limit or format statements, and broken references. Use
`inspect_visual` for PDF-level evidence of severe layout problems,
blank/corrupted pages, missing central visuals, unreadably small text, or
non-inspectable artifacts. Only flag a desk-reject risk when evidence is
explicit; otherwise say no such risk was confirmed from the inspected evidence.

Prefer `search_file` for sections, figure/table mentions, definitions,
limitations, and appendix references. Use `read_file` to inspect the exact
surrounding prose before judging clarity.

For Presentation questions, use `search_file` and `read_file` before judging
captions, surrounding prose, equations, algorithms, page-local explanation, or
table contents. Use `inspect_visual` before judging actual visual readability,
layout, figure/table legibility, typography, overlap, truncation, or whether a
specific page is visually easy to inspect.

Use `inspect_visual` with one specific target at a time:

- For figure contents and figure readability, target `Figure N`; the tool will
  prefer the extracted figure asset from the paper's `figures/` directory.
- For figure page placement, caption crowding, or whether the figure is too
  small on the page, target `Figure N` and set the focus to page layout.
- For table visual formatting, target `Table N`; table contents should still be
  read with `search_file` and `read_file`.
- For general page formatting, target `page N`.

If a figure or table cannot be visually inspected, report that limitation as
evidence availability, then use available captions, surrounding prose, paper
text, or VLM observations to make supported claims. Mark a weakness when there
is confirmed evidence of unclear prose, inconsistent references, missing
definitions, illegible/overloaded visuals, incomplete captions, cramped layout,
or ambiguous experimental explanation.

When assessing figures and tables, distinguish:

- confirmed issue: e.g. caption does not explain the plotted metric, labels are
  unreadable in VLM/PDF evidence, table omits metric definitions, or text never
  explains the figure's conclusion.
- unavailable evidence: e.g. image could not be inspected. Treat this as an
  evidence limitation.

Use `search_scholar` only when the question explicitly concerns related-work
coverage, citation correctness, or terminology relative to the literature.

<!--
Purpose: Top-level documentation for the Reviewer repository.
It explains the intended workflow and where future implementation should live.
-->

# Reviewer

Reviewer is a structured review-agent repository for paper evaluation.

The workflow is:

1. Build an XML paper summary.
2. Run three dimension agents aligned with ICLR-style review dimensions:
   Contribution, Soundness, and Presentation.
3. Let each dimension agent follow a Q&A trajectory.
4. Require every Q&A answer to include its review impact.
5. Aggregate the three dimension reviews into a final review.

This repository currently contains the engineering scaffold. Each file includes
a short purpose note so the implementation can be filled in module by module.


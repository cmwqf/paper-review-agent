<!--
Purpose: XML output contract for the final aggregated review.
-->

Return exactly one `<final_review>` XML document with final_score, summary,
strengths, weaknesses, requested_changes, and confidence.

Use this structure:

```xml
<final_review>
  <final_score>1-10</final_score>
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
  <dimension_scores>
    <dimension name="Contribution">...</dimension>
    <dimension name="Soundness">...</dimension>
    <dimension name="Presentation">...</dimension>
  </dimension_scores>
  <confidence>low | medium | high</confidence>
</final_review>
```

The final score should synthesize the three dimension reviews. It should not
blindly average them if one dimension contains a critical weakness.

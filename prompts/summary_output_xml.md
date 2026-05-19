<!--
Purpose: XML contract for the paper summary generated before dimension review.
-->

Return exactly one `<paper_summary>` XML document.

Use this structure:

```xml
<paper_summary>
  <metadata>
    <title>...</title>
    <authors>...</authors>
    <venue>...</venue>
    <submission_date>...</submission_date>
  </metadata>
  <paper_map>
    <section>
      <section_id>s1</section_id>
      <title>Introduction</title>
      <summary>One to three factual sentences about what this section contains.</summary>
      <key_items>
        <item>
          <type>problem | motivation | claim | method_component | dataset | baseline | ablation | metric | result | stated_limitation | other</type>
          <text>Short factual item from this section.</text>
          <location_hint>Optional explicit location such as Table 3, Figure 2, Algorithm 1, Equation 4, Section 4.2, or Appendix A.</location_hint>
        </item>
      </key_items>
    </section>
  </paper_map>
  <global_index>
    <claims>
      <item section_ref="s1">...</item>
    </claims>
    <method_components>
      <item section_ref="s2">...</item>
    </method_components>
    <datasets>
      <item section_ref="s4">...</item>
    </datasets>
    <baselines>
      <item section_ref="s4">...</item>
    </baselines>
    <ablations>
      <item section_ref="s4">...</item>
    </ablations>
    <metrics>
      <item section_ref="s4">...</item>
    </metrics>
    <results>
      <item section_ref="s4">...</item>
    </results>
    <stated_limitations>
      <item section_ref="s5">...</item>
    </stated_limitations>
  </global_index>
</paper_summary>
```

Keep each section summary compact. Do not turn the paper map into a full review
or a long detailed summary.

Use at most 8 sections. Use at most 6 key_items per section. Use short text in
each item. Avoid copying long paragraphs from the paper.

Use `<location_hint>` only when the paper explicitly ties the item to a table,
figure, algorithm, equation, appendix, or numbered section. If there is no
explicit location, omit `<location_hint>`. Do not invent location hints.

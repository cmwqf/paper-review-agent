<!--
Purpose: XML output contract for generating Semantic Scholar queries and tags.
-->

Return exactly one `<retrieval_queries>` XML document containing search tags,
expanded queries, and optional time-filter hints.

Use this structure:

```xml
<retrieval_queries>
  <tags>
    <tag>...</tag>
  </tags>
  <queries>
    <query>...</query>
  </queries>
  <time_filter_hint>before_submission | none</time_filter_hint>
</retrieval_queries>
```

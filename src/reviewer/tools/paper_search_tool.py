"""Purpose: Search within the reviewed paper by keyword.

PaperSearchTool is a local evidence-navigation tool. It should accept a query
keyword and return compact line references with short snippets. It should not
return long raw chunks by default.

- search paper text for keyword matches
- return line references, score, and compact snippets
- keep results compact for Agent context
- support a future upgrade from keyword search to embedding retrieval
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PaperSearchResult:
    """Compact reference to a paper chunk found by paper-local search."""

    chunk_id: str
    snippet: str
    score: float | None = None
    section_id: str | None = None
    section_title: str | None = None
    keyword: str | None = None
    matched_line: int | None = None
    start_line: int | None = None
    end_line: int | None = None


class PaperSearchTool:
    """Search the reviewed paper and return PaperBench-style observations."""

    def __init__(self, config: dict):
        self.config = config

    def search_results(
        self,
        keyword: str,
        paper: dict,
        *,
        context_lines: int = 2,
        max_matches: int | None = None,
    ) -> list[PaperSearchResult]:
        """Return structured keyword locations with local context.

        Search is case-insensitive. Each result contains the matched line and
        symmetric context, using 1-based line numbers.
        """
        cleaned_keyword = keyword.strip()
        if not cleaned_keyword:
            raise ValueError("keyword must not be empty.")
        if context_lines < 0:
            raise ValueError("context_lines must be >= 0.")
        if max_matches is not None and max_matches < 1:
            raise ValueError("max_matches must be >= 1.")

        lines = str(paper.get("text") or "").splitlines()
        lowered_keyword = cleaned_keyword.lower()
        results: list[PaperSearchResult] = []
        for index, line in enumerate(lines):
            if lowered_keyword not in line.lower():
                continue
            start_index = max(0, index - context_lines)
            end_index = min(len(lines), index + context_lines + 1)
            start_line = start_index + 1
            end_line = end_index
            snippet_lines = []
            for line_index in range(start_index, end_index):
                prefix = ">>> " if line_index == index else "    "
                snippet_lines.append(f"{prefix}{line_index + 1}: {lines[line_index]}")
            snippet = "\n".join(snippet_lines)
            results.append(
                PaperSearchResult(
                    chunk_id=f"L{start_line}-L{end_line}",
                    snippet=snippet,
                    score=1.0,
                    keyword=cleaned_keyword,
                    matched_line=index + 1,
                    start_line=start_line,
                    end_line=end_line,
                )
            )
            if max_matches is not None and len(results) >= max_matches:
                break
        return results

    def search(
        self,
        keyword: str,
        paper: dict,
        top_k: int = 5,
        *,
        context_lines: int = 2,
        page: int = 1,
    ) -> str:
        """Return a compact text observation for keyword search."""
        cleaned_keyword = keyword.strip()
        if not cleaned_keyword:
            raise ValueError("keyword must not be empty.")
        if top_k < 1:
            raise ValueError("top_k must be >= 1.")
        if page < 1:
            raise ValueError("page must be >= 1.")

        all_results = self.search_results(
            cleaned_keyword,
            paper,
            context_lines=context_lines,
            max_matches=None,
        )
        if not all_results:
            return f"No matches found for '{cleaned_keyword}'."

        total_matches = len(all_results)
        total_pages = (total_matches + top_k - 1) // top_k
        if page > total_pages:
            return f"Invalid page number. There are only {total_pages} pages of results."

        start_index = (page - 1) * top_k
        end_index = min(start_index + top_k, total_matches)
        page_results = all_results[start_index:end_index]

        matches = [
            f"[Match {match_index} of {total_matches}]\n{result.snippet}"
            for match_index, result in enumerate(page_results, start=start_index + 1)
        ]
        return "\n\n".join(matches)

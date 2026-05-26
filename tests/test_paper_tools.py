"""Purpose: Tests for local paper read/search evidence tools."""

from __future__ import annotations

import pytest

from reviewer.tools import PaperPDFReadTool, PaperReadTool, PaperSearchTool


def test_read_file_reads_1_based_line_range() -> None:
    """PaperReadTool should return the requested bounded line range."""
    paper = {"text": "line 1\nline 2\nline 3\nline 4"}

    result = PaperReadTool({}).read_result(paper, start_line=2, num_lines=2)

    assert result.ref_id == "L2-L3"
    assert result.start_line == 2
    assert result.end_line == 3
    assert result.text == "line 2\nline 3"


def test_read_file_caps_requests_at_50_lines() -> None:
    """PaperReadTool should reject overly large reads."""
    paper = {"text": "\n".join(f"line {index}" for index in range(1, 60))}

    with pytest.raises(ValueError, match="num_lines must be <= 50"):
        PaperReadTool({}).read_result(paper, start_line=1, num_lines=51)


def test_read_file_rejects_out_of_range_start_line() -> None:
    """PaperReadTool should reject a start line beyond the paper."""
    paper = {"text": "line 1\nline 2"}

    with pytest.raises(ValueError, match="exceeds paper length"):
        PaperReadTool({}).read_result(paper, start_line=3, num_lines=1)


def test_read_file_returns_paperbench_style_observation() -> None:
    """PaperReadTool.read should return text meant for model observation."""
    paper = {"text": "line 1\nline 2\nline 3\nline 4"}

    observation = PaperReadTool({}).read(paper, start_line=2, num_lines=2)

    assert observation == "2: line 2\n3: line 3"


def test_search_file_returns_keyword_locations_with_context() -> None:
    """PaperSearchTool should return matched lines with symmetric context."""
    paper = {
        "text": "\n".join(
            [
                "Intro",
                "We compare against strong Baselines.",
                "Context 1",
                "Context 2",
                "Context 3",
                "Context 4",
                "Context 5",
                "Context 6",
                "More baselines appear here.",
                "Tail",
            ]
        )
    }

    results = PaperSearchTool({}).search_results("baselines", paper, context_lines=2)

    assert len(results) == 2
    assert results[0].chunk_id == "L1-L4"
    assert results[0].matched_line == 2
    assert results[0].start_line == 1
    assert results[0].end_line == 4
    assert results[0].snippet == "\n".join(
        [
            "    1: Intro",
            ">>> 2: We compare against strong Baselines.",
            "    3: Context 1",
            "    4: Context 2",
        ]
    )


def test_search_file_honors_top_k() -> None:
    """PaperSearchTool should return only the first top_k matches."""
    paper = {"text": "baseline one\nx\nbaseline two\nx\nbaseline three"}

    results = PaperSearchTool({}).search_results("baseline", paper, max_matches=2)

    assert [result.matched_line for result in results] == [1, 3]


def test_search_file_returns_paperbench_style_observation() -> None:
    """PaperSearchTool.search should return text meant for model observation."""
    paper = {"id": "abc", "text": "baseline one\nx\nbaseline two\nx\nbaseline three"}

    observation = PaperSearchTool({}).search("baseline", paper, top_k=2, context_lines=1)

    assert "[Match 1 of 3]" in observation
    assert ">>> 1: baseline one" in observation
    assert "[Match 2 of 3]" in observation
    assert ">>> 3: baseline two" in observation


def test_read_pdf_reads_1_based_page_range() -> None:
    """PaperPDFReadTool should return requested PDF pages."""
    paper = {"pdf_pages": ["first page", "second page", "third page"]}

    result = PaperPDFReadTool({}).read_result(paper, start_page=2, num_pages=2)

    assert result.ref_id == "P2-P3"
    assert result.start_page == 2
    assert result.end_page == 3
    assert result.text == "Page 2:\nsecond page\n\nPage 3:\nthird page"


def test_read_pdf_rejects_large_page_reads() -> None:
    """PaperPDFReadTool should cap page reads."""
    paper = {"pdf_pages": ["first page", "second page"]}

    with pytest.raises(ValueError, match="num_pages must be <= 1"):
        PaperPDFReadTool({"paper": {"max_pdf_read_pages": 1}}).read_result(
            paper,
            start_page=1,
            num_pages=2,
        )

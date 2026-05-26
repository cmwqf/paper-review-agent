"""Purpose: Read exact paper evidence by line range.

PaperReadTool is an evidence-access tool. It should read full text for a
specific line range after PaperSearchTool has identified likely relevant
locations.

- read by 1-based line number
- cap each read to a small bounded range
- return raw paper text for the current Answer Agent step
- save raw text in full trace, but avoid carrying it into future prompts
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PaperReadResult:
    """Raw paper text returned for one requested reference."""

    ref_id: str
    text: str
    start_line: int
    end_line: int
    section_id: str | None = None
    section_title: str | None = None


class PaperReadTool:
    """Read exact text from the reviewed paper by line range."""

    def __init__(self, config: dict):
        self.config = config

    def read_result(self, paper: dict, start_line: int, num_lines: int = 50) -> PaperReadResult:
        """Return structured raw paper text for a bounded 1-based line range.

        Args:
            paper: Normalized paper dictionary containing a ``text`` field.
            start_line: 1-based initial line to read.
            num_lines: Number of lines to read. Must be between 1 and 50.
        """
        if start_line < 1:
            raise ValueError("start_line must be >= 1.")
        if num_lines < 1:
            raise ValueError("num_lines must be >= 1.")
        if num_lines > 50:
            raise ValueError("num_lines must be <= 50.")

        lines = str(paper.get("text") or "").splitlines()
        if not lines:
            return PaperReadResult(ref_id="L0-L0", text="", start_line=0, end_line=0)
        if start_line > len(lines):
            raise ValueError(f"start_line {start_line} exceeds paper length {len(lines)}.")

        start_index = start_line - 1
        end_index = min(start_index + num_lines, len(lines))
        end_line = end_index
        text = "\n".join(lines[start_index:end_index])
        return PaperReadResult(
            ref_id=f"L{start_line}-L{end_line}",
            text=text,
            start_line=start_line,
            end_line=end_line,
        )

    def read(self, paper: dict, start_line: int, num_lines: int = 50) -> str:
        """Return a compact text observation for a line range."""
        result = self.read_result(paper, start_line=start_line, num_lines=num_lines)
        if result.start_line == 0:
            return ""

        lines = result.text.splitlines()
        numbered_lines = [
            f"{line_number}: {line}"
            for line_number, line in enumerate(lines, start=result.start_line)
        ]
        return "\n".join(numbered_lines)

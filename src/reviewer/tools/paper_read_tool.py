"""Purpose: Scaffold for reading exact paper evidence by reference.

PaperReadTool is an evidence-access tool. It should read full text for a
specific chunk_id, section_id, or character range after PaperSearchTool has
identified likely relevant locations.

Planned responsibilities:

- read by chunk_id
- read by section_id
- optionally read by char range
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
    section_id: str | None = None
    section_title: str | None = None


class PaperReadTool:
    """Read exact text from the reviewed paper by reference."""

    def __init__(self, config: dict):
        self.config = config

    def read(self, ref_id: str, paper: dict, max_chars: int | None = None) -> PaperReadResult:
        """Return raw paper text for one chunk, section, or range reference."""
        raise NotImplementedError("PaperReadTool.read is scaffolded.")

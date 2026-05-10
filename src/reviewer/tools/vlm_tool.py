"""Purpose: VLM tool for page-level and figure-level presentation checks."""

from __future__ import annotations


class VLMTool:
    """Analyze rendered PDF pages or figures for presentation quality."""

    def __init__(self, config: dict):
        self.config = config

    def inspect_pages(self, page_images: list[str], questions: list[str]) -> str:
        """Return XML or text observations from a VLM."""
        raise NotImplementedError("VLMTool.inspect_pages is scaffolded.")


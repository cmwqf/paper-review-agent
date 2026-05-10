"""Purpose: Abstract model interfaces used by agents and tools."""

from __future__ import annotations

from typing import Protocol


class TextModel(Protocol):
    """Protocol for text-generation models."""

    def generate(self, messages: list[dict], **kwargs: object) -> str:
        """Generate text from chat-style messages."""
        ...


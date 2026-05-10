"""Purpose: Define review dimensions shared by agents, schemas, and prompts."""

from __future__ import annotations

from enum import Enum


class ReviewDimension(str, Enum):
    """ICLR-aligned dimensions used by this workflow."""

    CONTRIBUTION = "Contribution"
    SOUNDNESS = "Soundness"
    PRESENTATION = "Presentation"

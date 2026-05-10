"""Purpose: VLM client implementation for presentation-page inspection."""

from __future__ import annotations


class VLMClient:
    """OpenAI-compatible VLM client placeholder."""

    def __init__(self, model_config: dict):
        self.model_config = model_config

    def generate_with_images(self, messages: list[dict], image_paths: list[str]) -> str:
        """Call the configured VLM with rendered page images."""
        raise NotImplementedError("VLMClient.generate_with_images is scaffolded.")


"""Purpose: OpenAI-compatible VLM client for presentation-page inspection."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any

from reviewer.models.llm_client import LLMClient


class VLMClient:
    """Call an OpenAI-compatible vision chat-completions model."""

    def __init__(self, model_config: dict[str, Any], global_config: dict[str, Any] | None = None):
        self.model_config = model_config
        self.client = LLMClient(model_config, global_config=global_config)

    def generate_with_images(self, messages: list[dict[str, Any]], image_paths: list[str]) -> str:
        """Call the configured VLM with rendered page images."""
        if not image_paths:
            raise ValueError("generate_with_images requires at least one image path.")
        return self.client.generate(_messages_with_images(messages, image_paths))


def _messages_with_images(
    messages: list[dict[str, Any]],
    image_paths: list[str],
) -> list[dict[str, Any]]:
    """Attach image_url content blocks to the final user message."""
    if not messages:
        raise ValueError("messages must not be empty.")
    prepared = [dict(message) for message in messages]
    user_index = _last_user_message_index(prepared)
    content = _content_blocks(prepared[user_index].get("content", ""))
    for path in image_paths:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": _image_data_url(path),
                },
            }
        )
    prepared[user_index]["content"] = content
    return prepared


def _last_user_message_index(messages: list[dict[str, Any]]) -> int:
    """Return the index of the final user message."""
    for index in range(len(messages) - 1, -1, -1):
        if messages[index].get("role") == "user":
            return index
    raise ValueError("messages must include a user message for image input.")


def _content_blocks(content: Any) -> list[dict[str, Any]]:
    """Normalize message content to OpenAI multimodal content blocks."""
    if isinstance(content, list):
        return list(content)
    return [{"type": "text", "text": str(content)}]


def _image_data_url(path: str) -> str:
    """Encode a local image path as a data URL."""
    image_path = Path(path)
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"

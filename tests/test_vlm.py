"""Purpose: Tests for VLM client/tool wiring without network calls."""

from __future__ import annotations

import base64

from reviewer.models.vlm_client import VLMClient
from reviewer.tools.vlm_tool import VLMTool


class FakeLLMClient:
    def __init__(self):
        self.messages = None

    def generate(self, messages):
        self.messages = messages
        return "visual observation"


class FakeVLMClient:
    def __init__(self):
        self.calls = []

    def generate_with_images(self, messages, image_paths):
        self.calls.append((messages, image_paths))
        return "figures are legible"


def test_vlm_client_attaches_images_as_data_urls(tmp_path):
    """VLMClient should send image_url content blocks."""
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"image-bytes")
    fake = FakeLLMClient()
    client = VLMClient.__new__(VLMClient)
    client.model_config = {}
    client.client = fake

    output = client.generate_with_images(
        [{"role": "user", "content": "inspect"}],
        [str(image_path)],
    )

    assert output == "visual observation"
    content = fake.messages[0]["content"]
    assert content[0] == {"type": "text", "text": "inspect"}
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"] == (
        "data:image/png;base64," + base64.b64encode(b"image-bytes").decode("ascii")
    )


def test_vlm_tool_calls_configured_vlm_model(monkeypatch):
    """VLMTool should call build_vlm and pass page images."""
    fake_client = FakeVLMClient()
    monkeypatch.setattr("reviewer.tools.vlm_tool.build_vlm", lambda config, model_key: fake_client)

    output = VLMTool({"agents": {"presentation": {"vlm_model": "vlm"}}}).inspect_pages(
        ["page_1.png"],
        ["Are figures legible?"],
    )

    assert output == "figures are legible"
    assert fake_client.calls[0][1] == ["page_1.png"]
    assert "Are figures legible?" in fake_client.calls[0][0][1]["content"]

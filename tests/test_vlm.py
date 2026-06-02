"""Purpose: Tests for VLM client/tool wiring without network calls."""

from __future__ import annotations

import base64

from reviewer.models.vlm_client import VLMClient
from reviewer.tools.visual_inspection_tool import VisualInspectionTool
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


def test_visual_inspection_uses_figure_asset_by_default(monkeypatch, tmp_path):
    """inspect_visual should route Figure targets to extracted figure assets."""
    image_path = tmp_path / "_page_4_Figure_2.jpeg"
    image_path.write_bytes(b"image")
    calls = []

    def fake_inspect_pages(self, page_images, questions):
        calls.append((page_images, questions))
        return "Figure labels are readable."

    monkeypatch.setattr("reviewer.tools.visual_inspection_tool.VLMTool.inspect_pages", fake_inspect_pages)

    output = VisualInspectionTool({"agents": {"presentation": {"use_vlm": True}}}).inspect(
        {
            "id": "paper",
            "figures": [
                {
                    "label": "Figure 2",
                    "path": str(image_path),
                    "pdf_page": 5,
                }
            ],
            "metadata": {"source_path": str(tmp_path / "paper.pdf")},
        },
        target="Figure 2",
        focus="axis and legend readability",
    )

    assert calls[0][0] == [str(image_path)]
    assert "extracted figure asset" in calls[0][1][0]
    assert "kind: figure_asset" in output
    assert "Figure labels are readable." in output


def test_visual_inspection_routes_layout_to_one_pdf_page(monkeypatch, tmp_path):
    """Figure page-layout requests should render exactly one corresponding PDF page."""
    rendered = tmp_path / "page_5.png"
    calls = []

    def fake_render(source_path, output_dir, start_page, num_pages, dpi):
        calls.append((source_path, output_dir, start_page, num_pages, dpi))
        return [str(rendered)]

    def fake_inspect_pages(self, page_images, questions):
        calls.append((page_images, questions))
        return "Figure is not too small on the page."

    monkeypatch.setattr("reviewer.tools.visual_inspection_tool.render_pdf_page_range", fake_render)
    monkeypatch.setattr("reviewer.tools.visual_inspection_tool.VLMTool.inspect_pages", fake_inspect_pages)

    output = VisualInspectionTool(
        {"agents": {"presentation": {"use_vlm": True}}, "paper": {"page_image_dpi": 220}}
    ).inspect(
        {
            "id": "paper",
            "figures": [
                {
                    "label": "Figure 2",
                    "path": str(tmp_path / "_page_4_Figure_2.jpeg"),
                    "pdf_page": 5,
                }
            ],
            "metadata": {"source_path": str(tmp_path / "paper.pdf")},
        },
        target="Figure 2",
        focus="page layout and caption placement",
    )

    assert calls[0][2:4] == (5, 1)
    assert calls[1][0] == [str(rendered)]
    assert "kind: pdf_page" in output
    assert "pdf_page: 5" in output


def test_visual_inspection_routes_table_to_one_pdf_page(monkeypatch, tmp_path):
    """Table targets should use one PDF page for visual formatting checks."""
    rendered = tmp_path / "page_3.png"
    calls = []

    def fake_extract(source_path):
        return ["intro", "Table 1: Results\nrows", "appendix"]

    def fake_render(source_path, output_dir, start_page, num_pages, dpi):
        calls.append((start_page, num_pages))
        return [str(rendered)]

    def fake_inspect_pages(self, page_images, questions):
        calls.append((page_images, questions))
        return "Table is visually scannable."

    monkeypatch.setattr("reviewer.tools.visual_inspection_tool.extract_pdf_pages", fake_extract)
    monkeypatch.setattr("reviewer.tools.visual_inspection_tool.render_pdf_page_range", fake_render)
    monkeypatch.setattr("reviewer.tools.visual_inspection_tool.VLMTool.inspect_pages", fake_inspect_pages)

    output = VisualInspectionTool({"agents": {"presentation": {"use_vlm": True}}}).inspect(
        {"id": "paper", "metadata": {"source_path": str(tmp_path / "paper.pdf")}},
        target="Table 1",
        focus="visual formatting",
    )

    assert calls[0] == (2, 1)
    assert calls[1][0] == [str(rendered)]
    assert "kind: pdf_page" in output
    assert "pdf_page: 2" in output

"""Purpose: VLM tool for page-level and figure-level presentation checks."""

from __future__ import annotations

from reviewer.models.factory import build_vlm


class VLMTool:
    """Analyze rendered PDF pages or figures for presentation quality."""

    def __init__(self, config: dict):
        self.config = config

    def inspect_pages(self, page_images: list[str], questions: list[str]) -> str:
        """Return VLM observations for rendered PDF pages."""
        if not page_images:
            raise ValueError("inspect_pages requires at least one page image.")
        model_key = (
            self.config.get("agents", {})
            .get("presentation", {})
            .get("vlm_model", "vlm")
        )
        client = build_vlm(self.config, str(model_key))
        prompt = _inspect_prompt(questions)
        return client.generate_with_images(
            [
                {
                    "role": "system",
                    "content": (
                        "You inspect academic paper page images for presentation quality. "
                        "Focus on visual readability, figures, tables, captions, equations, "
                        "layout, and formatting. Keep novelty and technical soundness separate."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            page_images,
        )


def _inspect_prompt(questions: list[str]) -> str:
    """Build a concise VLM inspection prompt."""
    if questions:
        question_text = "\n".join(f"- {question}" for question in questions)
    else:
        question_text = (
            "- Are figures and tables legible?\n"
            "- Are captions informative?\n"
            "- Are there layout or formatting issues?"
        )
    return (
        "Inspect the attached PDF page images and answer these presentation questions:\n"
        f"{question_text}\n\n"
        "Return concise bullet observations with page numbers when possible."
    )

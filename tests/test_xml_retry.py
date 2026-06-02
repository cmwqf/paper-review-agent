"""Purpose: Tests for XML regeneration retries."""

from __future__ import annotations

from reviewer.utils.xml_retry import generate_valid_xml


class FakeClient:
    """Return predefined XML outputs and capture prompts."""

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def generate(self, messages):
        self.calls.append(messages)
        return self.outputs.pop(0)


def test_generate_valid_xml_retries_parse_errors() -> None:
    client = FakeClient(
        [
            "<final_review><summary>bad & text</summary></final_review>",
            "<final_review><summary>good &amp; text</summary></final_review>",
        ]
    )

    xml = generate_valid_xml(
        client=client,
        root_tag="final_review",
        max_attempts=2,
        messages=[{"role": "user", "content": "write xml"}],
    )

    assert xml == "<final_review><summary>good &amp; text</summary></final_review>"
    assert len(client.calls) == 2
    assert "not valid <final_review> XML" in client.calls[1][-1]["content"]

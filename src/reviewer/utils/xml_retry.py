"""Purpose: Retry model XML generation when the output is not parseable."""

from __future__ import annotations

from typing import Any

from reviewer.tools.xml_validator import validate_xml_root


def generate_valid_xml(
    *,
    client: Any,
    messages: list[dict[str, Any]],
    root_tag: str,
    max_attempts: int = 5,
    trace_events: list[dict[str, Any]] | None = None,
    trace_base: dict[str, Any] | None = None,
) -> str:
    """Generate model output until it validates as XML with the requested root."""
    attempts = max(1, int(max_attempts))
    current_messages = list(messages)
    last_error: Exception | None = None
    last_output = ""
    for attempt in range(1, attempts + 1):
        raw_output = client.generate(current_messages)
        last_output = raw_output
        if trace_events is not None:
            trace_events.append(
                {
                    **(trace_base or {}),
                    "event": "model_output",
                    "attempt": attempt,
                    "raw_output": raw_output,
                }
            )
        try:
            return validate_xml_root(raw_output, root_tag)
        except Exception as exc:
            last_error = exc
            if attempt >= attempts:
                break
            current_messages = [
                *messages,
                {
                    "role": "assistant",
                    "content": raw_output,
                },
                {
                    "role": "user",
                    "content": (
                        f"The previous output was not valid <{root_tag}> XML.\n"
                        f"Parser error: {type(exc).__name__}: {exc}\n\n"
                        "Regenerate the whole document. Output only one valid XML document. "
                        "Do not wrap it in markdown fences. Escape all literal &, <, and > "
                        "characters in text content as XML entities."
                    ),
                },
            ]
    assert last_error is not None
    raise RuntimeError(
        f"Could not generate valid <{root_tag}> XML after {attempts} attempts: "
        f"{type(last_error).__name__}: {last_error}\nLast output:\n{last_output}"
    )

"""Purpose: Generate text via the local Claude Code CLI instead of an HTTP API.

This client mirrors :class:`LLMClient.generate` so agents can switch backend by
setting ``provider: claude_code`` in a model config, with no agent-side changes.

Design constraints (see docs/CONFIG_AND_MODEL_CLIENT.md):

- Claude must behave as a pure text generator. None of Claude Code's built-in
  tools (Read/Bash/WebSearch/Edit/...) may run; the reviewer's own tools are
  orchestrated in Python by parsing the model's XML output, never via native
  tool-calling. We enforce this with ``--tools ""`` which removes every
  built-in tool from the model's view (unlike ``--allowed-tools``, which only
  gates permission and still lets the model emit a tool_use), plus
  ``--max-turns 1`` as a backstop.
- The reviewer supplies its own complete system prompt, so we use
  ``--system-prompt`` (replace) rather than ``--append-system-prompt`` to strip
  Claude Code's default tool-oriented persona.

Sampling parameters (temperature/top_p/max_tokens) have no CLI equivalent and
are intentionally ignored on this path.
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

from reviewer.models.llm_client import LLMClient
from reviewer.settings import ConfigError

LOGGER = logging.getLogger(__name__)

# Process-global accumulator of per-call Claude Code usage, so a run can emit a
# usage.json artifact regardless of text-log configuration. Scoped to a single
# run via reset_usage_log(); a concurrent batch shares it, so prefer per-run
# usage from the text log when running many papers at once.
_USAGE_LOG: list[dict[str, Any]] = []


def reset_usage_log() -> None:
    """Clear the global Claude Code usage accumulator."""
    _USAGE_LOG.clear()


def usage_summary() -> dict[str, Any]:
    """Aggregate accumulated Claude Code usage into a compact summary."""
    calls = list(_USAGE_LOG)

    def _sum(key: str) -> int:
        return sum(int(c.get(key) or 0) for c in calls)

    cache_read = _sum("cache_read_input_tokens")
    cache_create = _sum("cache_creation_input_tokens")
    cache_hit_calls = sum(1 for c in calls if int(c.get("cache_read_input_tokens") or 0) > 0)
    by_model: dict[str, int] = {}
    for c in calls:
        by_model[str(c.get("model"))] = by_model.get(str(c.get("model")), 0) + 1
    return {
        "calls": len(calls),
        "calls_by_model": by_model,
        "total_cost_usd": round(sum(float(c.get("cost_usd") or 0.0) for c in calls), 4),
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_create,
        "output_tokens": _sum("output_tokens"),
        "cache_hit_calls": cache_hit_calls,
        "cache_hit_rate": round(cache_hit_calls / len(calls), 3) if calls else 0.0,
    }


def make_text_client(
    model_config: dict[str, Any], global_config: dict[str, Any] | None = None
) -> Any:
    """Build a text client for a model config, dispatching on ``provider``.

    ``provider`` defaults to ``openai`` (the OpenAI-compatible HTTP client), so
    existing configs are unaffected. ``claude_code`` routes to the local CLI.
    """
    provider = str(model_config.get("provider") or "openai").strip().lower().replace("-", "_")
    if provider in ("claude_code", "claudecode"):
        return ClaudeCodeClient(model_config, global_config=global_config)
    if provider in ("", "openai", "openai_compatible"):
        return LLMClient(model_config, global_config=global_config)
    raise ConfigError(f"Unknown model provider: {provider!r}")


class ClaudeCodeError(RuntimeError):
    """A Claude Code CLI invocation failed or returned an error result."""


class ClaudeSessionLimitError(ClaudeCodeError):
    """The Claude subscription session/usage limit was hit.

    Retrying does not help until the limit resets (hours away), so callers must
    fail fast rather than burn retries/backoff on it.
    """


@dataclass
class ClaudeCodeClient:
    """Text generation backed by the Claude Code CLI in headless print mode."""

    model_config: dict[str, Any]
    global_config: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self.global_config = self.global_config or {}
        self.model = str(self.model_config.get("model") or "").strip()
        if not self.model:
            raise ConfigError("Model config must define model.")
        self.cli_command = str(self.model_config.get("cli_command") or "claude").strip()
        # `--tools ""` removes all built-in tools from the model's view, so it
        # never emits a tool_use. (`--allowed-tools` only gates permission.)
        self.tools = str(self.model_config.get("tools", ""))
        self.max_turns = int(self.model_config.get("max_turns", 1))
        extra = self.model_config.get("extra_cli_args") or []
        self.extra_cli_args = [str(item) for item in extra] if isinstance(extra, list) else []

    def _base_command(self, system_prompt: str, *, stream: bool) -> list[str]:
        """Assemble the CLI command shared by text and image requests.

        Image input uses ``--input-format stream-json``, which the CLI requires
        be paired with ``--output-format stream-json`` (plus ``--verbose``);
        text input uses the simpler single-object ``--output-format json``.
        """
        command = [
            self.cli_command,
            "-p",
            "--model",
            self.model,
            "--max-turns",
            str(self.max_turns),
            "--exclude-dynamic-system-prompt-sections",
        ]
        if stream:
            command += ["--input-format", "stream-json", "--output-format", "stream-json", "--verbose"]
        else:
            command += ["--output-format", "json"]
        if system_prompt:
            command += ["--system-prompt", system_prompt]
        # Keep --tools followed by another arg so its variadic value does not
        # greedily swallow later tokens.
        command += ["--tools", self.tools]
        command += self.extra_cli_args
        return command

    def generate(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        """Call the Claude Code CLI and return the assistant text.

        ``messages`` follows the OpenAI shape used across the project. System
        messages become ``--system-prompt``. If any message carries image
        content blocks, the conversation is sent via ``--input-format
        stream-json`` so images pass as base64 without enabling any tool.
        """
        timeout = float(kwargs.pop("timeout_seconds", self.model_config.get("timeout_seconds", 180)))
        max_retries = int(kwargs.pop("max_retries", self.model_config.get("max_retries", 3)))

        system_prompt = _join_system(messages)
        turns = [message for message in messages if message.get("role") != "system"]
        has_images = _messages_have_images(turns)

        command = self._base_command(system_prompt, stream=has_images)
        stdin_text = _stream_json_stdin(turns) if has_images else _flatten_turns(turns)

        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                completed = subprocess.run(
                    command,
                    input=stdin_text,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                output = self._parse_result(completed, stream=has_images)
                if not output.strip():
                    raise ClaudeCodeError(
                        f"Claude Code returned empty content (stderr={completed.stderr.strip()!r})."
                    )
                return output
            except Exception as exc:
                LOGGER.warning(
                    "Claude Code call attempt %s/%s failed: model=%s cli=%s error=%r",
                    attempt,
                    max_retries,
                    self.model,
                    self.cli_command,
                    exc,
                )
                last_error = exc
                # The session/usage limit won't clear within retries — fail fast.
                if isinstance(exc, ClaudeSessionLimitError):
                    break
                # Back off before retrying so a transient blip — e.g. the CLI
                # being upgraded (symlink briefly missing -> FileNotFoundError) or
                # a momentary rate-limit — has time to clear instead of burning
                # all retries in milliseconds.
                if attempt < max_retries:
                    time.sleep(min(2 * attempt, 10))
        assert last_error is not None
        raise last_error

    def _parse_result(self, completed: subprocess.CompletedProcess[str], *, stream: bool) -> str:
        """Extract assistant text from the CLI result.

        ``--output-format json`` emits one object; ``--output-format
        stream-json`` (used for image input) emits newline-delimited events, of
        which the final ``type: result`` event carries the text.
        """
        lowered = completed.stdout.lower()
        if "hit your session limit" in lowered or "not logged in" in lowered:
            # Session/usage limit OR a dropped login (e.g. after a CLI upgrade):
            # neither clears within the retry window, so fail fast.
            raise ClaudeSessionLimitError(
                f"Claude unavailable (session limit / not logged in): "
                f"{completed.stdout.strip()[:200]!r}"
            )
        if completed.returncode != 0:
            raise ClaudeCodeError(
                f"Claude Code CLI exited {completed.returncode}: "
                f"stderr={completed.stderr.strip()!r} stdout={completed.stdout.strip()[:500]!r}"
            )
        stdout = completed.stdout.strip()
        if not stdout:
            raise ClaudeCodeError(
                f"Claude Code CLI produced no stdout (stderr={completed.stderr.strip()!r})."
            )
        data = self._result_event(stdout) if stream else _loads(stdout)

        if isinstance(data, dict):
            if data.get("is_error"):
                raise ClaudeCodeError(
                    f"Claude Code reported an error result: subtype={data.get('subtype')!r} "
                    f"result={str(data.get('result'))[:500]!r}"
                )
            result = data.get("result")
            if isinstance(result, str):
                self._log_usage(data)
                return result
        raise ClaudeCodeError(f"Unexpected Claude Code result shape: {stdout[:500]!r}")

    def _log_usage(self, data: dict[str, Any]) -> None:
        """Record per-call cost and token usage (incl. prompt-cache reuse)."""
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        self.last_usage = {
            "model": self.model,
            "cost_usd": data.get("total_cost_usd"),
            "input_tokens": usage.get("input_tokens"),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
            "output_tokens": usage.get("output_tokens"),
        }
        # Accumulate globally so a run can write a usage.json artifact that does
        # not depend on the text log being configured/persisted.
        _USAGE_LOG.append(self.last_usage)
        LOGGER.info(
            "Claude Code usage: model=%s cost_usd=%s in=%s cache_create=%s cache_read=%s out=%s",
            self.model,
            self.last_usage["cost_usd"],
            self.last_usage["input_tokens"],
            self.last_usage["cache_creation_input_tokens"],
            self.last_usage["cache_read_input_tokens"],
            self.last_usage["output_tokens"],
        )

    @staticmethod
    def _result_event(stdout: str) -> dict[str, Any]:
        """Return the final ``type: result`` event from stream-json stdout."""
        result_event: dict[str, Any] | None = None
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and event.get("type") == "result":
                result_event = event
        if result_event is None:
            raise ClaudeCodeError(
                f"No result event in Claude Code stream-json output: {stdout[:500]!r}"
            )
        return result_event


def _loads(stdout: str) -> Any:
    """Parse a single-object ``--output-format json`` result."""
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ClaudeCodeError(f"Unable to parse Claude Code JSON output: {stdout[:500]!r}") from exc


def _join_system(messages: list[dict[str, Any]]) -> str:
    """Join all system messages into one replacement system prompt."""
    parts = [
        _text_of(message.get("content", ""))
        for message in messages
        if message.get("role") == "system"
    ]
    return "\n\n".join(part for part in parts if part.strip())


def _flatten_turns(turns: list[dict[str, Any]]) -> str:
    """Flatten non-system turns into a single stdin prompt.

    A lone user turn is sent verbatim. Multi-turn histories are rendered with
    role headers so the model still sees the prior exchange.
    """
    if len(turns) == 1 and turns[0].get("role") == "user":
        return _text_of(turns[0].get("content", ""))
    rendered = []
    for turn in turns:
        role = str(turn.get("role", "user")).capitalize()
        rendered.append(f"## {role}:\n{_text_of(turn.get('content', ''))}")
    return "\n\n".join(rendered)


def _text_of(content: Any) -> str:
    """Reduce OpenAI message content (string or block list) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "\n".join(parts)
    return str(content)


def _messages_have_images(turns: list[dict[str, Any]]) -> bool:
    """Return whether any turn carries an image content block."""
    for turn in turns:
        content = turn.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "image_url":
                    return True
    return False


def _stream_json_stdin(turns: list[dict[str, Any]]) -> str:
    """Render turns as newline-delimited stream-json user/assistant events."""
    lines = []
    for turn in turns:
        role = "assistant" if turn.get("role") == "assistant" else "user"
        blocks = _anthropic_blocks(turn.get("content", ""))
        event = {"type": role, "message": {"role": role, "content": blocks}}
        lines.append(json.dumps(event))
    return "\n".join(lines) + "\n"


def _anthropic_blocks(content: Any) -> list[dict[str, Any]]:
    """Convert OpenAI content into Anthropic-style content blocks."""
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if not isinstance(content, list):
        return [{"type": "text", "text": str(content)}]
    blocks: list[dict[str, Any]] = []
    for block in content:
        if not isinstance(block, dict):
            blocks.append({"type": "text", "text": str(block)})
            continue
        if block.get("type") == "text":
            blocks.append({"type": "text", "text": str(block.get("text", ""))})
        elif block.get("type") == "image_url":
            url = (block.get("image_url") or {}).get("url", "")
            blocks.append(_image_block_from_data_url(str(url)))
    return blocks


def _image_block_from_data_url(url: str) -> dict[str, Any]:
    """Parse a ``data:<mime>;base64,<data>`` URL into an Anthropic image block."""
    if not url.startswith("data:"):
        raise ClaudeCodeError(f"Claude Code image input requires a data URL, got: {url[:64]!r}")
    header, _, data = url.partition(",")
    media_type = header[len("data:") :].split(";", 1)[0] or "image/png"
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": data},
    }

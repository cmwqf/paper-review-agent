"""Purpose: Tests for the Claude Code CLI client without spawning the CLI."""

from __future__ import annotations

import json
import subprocess

import pytest

from reviewer.models.claude_code_client import (
    ClaudeCodeClient,
    ClaudeCodeError,
    CodexCliClient,
    make_text_client,
)
from reviewer.models.llm_client import LLMClient


class FakeCompleted:
    """Stand-in for subprocess.CompletedProcess."""

    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _patch_run(monkeypatch, *, result_text: str = "<xml>ok</xml>", capture: dict | None = None):
    """Patch subprocess.run to capture the invocation and return a result.

    Mirrors the CLI: stream-json input yields newline-delimited events; plain
    text input yields a single result object.
    """

    def fake_run(command, input=None, capture_output=None, text=None, timeout=None):
        if capture is not None:
            capture["command"] = command
            capture["input"] = input
        result = {"type": "result", "is_error": False, "result": result_text}
        if "stream-json" in command:
            stdout = (
                json.dumps({"type": "system", "subtype": "init"})
                + "\n"
                + json.dumps(result)
                + "\n"
            )
        else:
            stdout = json.dumps(result)
        return FakeCompleted(stdout=stdout)

    monkeypatch.setattr(subprocess, "run", fake_run)


def test_make_text_client_dispatches_on_provider() -> None:
    """provider routes to the right client; default stays OpenAI-compatible."""
    cc = make_text_client({"model": "opus", "provider": "claude_code"})
    assert isinstance(cc, ClaudeCodeClient)
    codex = make_text_client({"model": "gpt-5.6-sol", "provider": "codex_cli"})
    assert isinstance(codex, CodexCliClient)
    http = make_text_client({"model": "x", "base_url": "http://h/v1", "api_key_env": None})
    assert isinstance(http, LLMClient)


def test_generate_builds_locked_down_command(monkeypatch) -> None:
    """Text generation disables tools, caps turns, and replaces the system prompt."""
    capture: dict = {}
    _patch_run(monkeypatch, capture=capture)
    client = ClaudeCodeClient({"model": "opus", "provider": "claude_code"})

    out = client.generate(
        [
            {"role": "system", "content": "You are the reviewer."},
            {"role": "user", "content": "Review this paper."},
        ]
    )
    assert out == "<xml>ok</xml>"

    command = capture["command"]
    assert command[:2] == ["claude", "-p"]
    assert command[command.index("--tools") + 1] == ""  # no built-in tools
    assert command[command.index("--max-turns") + 1] == "1"  # no second turn
    assert command[command.index("--system-prompt") + 1] == "You are the reviewer."
    assert "--exclude-dynamic-system-prompt-sections" in command
    assert "--input-format" not in command  # text path, no stream-json
    # The lone user turn is sent verbatim on stdin.
    assert capture["input"] == "Review this paper."


def test_generate_flattens_multi_turn_history(monkeypatch) -> None:
    """Multi-turn histories are rendered with role headers on stdin."""
    capture: dict = {}
    _patch_run(monkeypatch, capture=capture)
    client = ClaudeCodeClient({"model": "opus", "provider": "claude_code"})

    client.generate(
        [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "second"},
        ]
    )
    assert capture["input"] == "## User:\nfirst\n\n## Assistant:\nreply\n\n## User:\nsecond"


def test_generate_with_images_uses_stream_json(monkeypatch) -> None:
    """Image content blocks switch to stream-json base64 input, still tool-free."""
    capture: dict = {}
    _patch_run(monkeypatch, capture=capture)
    client = ClaudeCodeClient({"model": "sonnet", "provider": "claude_code"})

    data_url = "data:image/png;base64,QUJD"
    client.generate(
        [
            {"role": "system", "content": "inspect"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "look"},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ]
    )
    command = capture["command"]
    assert command[command.index("--input-format") + 1] == "stream-json"
    # stream-json input requires stream-json output + --verbose.
    assert command[command.index("--output-format") + 1] == "stream-json"
    assert "--verbose" in command
    assert command[command.index("--tools") + 1] == ""  # still no Read tool

    event = json.loads(capture["input"].strip())
    blocks = event["message"]["content"]
    assert blocks[0] == {"type": "text", "text": "look"}
    assert blocks[1] == {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/png", "data": "QUJD"},
    }


def test_generate_raises_on_cli_error_result(monkeypatch) -> None:
    """An is_error result envelope is surfaced as ClaudeCodeError."""

    def fake_run(command, input=None, capture_output=None, text=None, timeout=None):
        body = json.dumps({"type": "result", "is_error": True, "subtype": "error_max_turns"})
        return FakeCompleted(stdout=body)

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = ClaudeCodeClient({"model": "opus", "provider": "claude_code", "max_retries": 1})
    with pytest.raises(ClaudeCodeError):
        client.generate([{"role": "user", "content": "hi"}])


def test_generate_raises_on_nonzero_exit(monkeypatch) -> None:
    """A non-zero CLI exit is surfaced with stderr context."""

    def fake_run(command, input=None, capture_output=None, text=None, timeout=None):
        return FakeCompleted(returncode=1, stderr="not logged in")

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = ClaudeCodeClient({"model": "opus", "provider": "claude_code", "max_retries": 1})
    with pytest.raises(ClaudeCodeError):
        client.generate([{"role": "user", "content": "hi"}])


def test_codex_cli_client_builds_exec_prompt(monkeypatch) -> None:
    """Codex provider runs codex exec with xhigh effort and a flattened prompt."""
    capture: dict = {}

    def fake_run(command, input=None, capture_output=None, text=None, timeout=None):
        capture["command"] = command
        capture["input"] = input
        capture["timeout"] = timeout
        return FakeCompleted(stdout="<xml>ok</xml>\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = CodexCliClient(
        {
            "model": "gpt-5.6-sol",
            "provider": "codex_cli",
            "reasoning_effort": "xhigh",
            "timeout_seconds": 123,
        }
    )

    out = client.generate(
        [
            {"role": "system", "content": "Return XML."},
            {"role": "user", "content": "Review this paper."},
        ]
    )

    assert out == "<xml>ok</xml>"
    command = capture["command"]
    assert command[:4] == ["codex", "exec", "-m", "gpt-5.6-sol"]
    assert 'model_reasoning_effort="xhigh"' in command
    assert "--dangerously-bypass-approvals-and-sandbox" in command
    assert command[-1] == "-"
    assert "Do not inspect files, run commands, or use tools." in capture["input"]
    assert "## System Instructions\nReturn XML." in capture["input"]
    assert "Review this paper." in capture["input"]
    assert capture["timeout"] == 123

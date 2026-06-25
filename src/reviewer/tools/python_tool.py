"""Purpose: Restricted Python calculation tool for evidence checks."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_IMPORTS = {
    "collections",
    "decimal",
    "fractions",
    "functools",
    "itertools",
    "json",
    "math",
    "operator",
    "re",
    "statistics",
}

FORBIDDEN_NAMES = {
    "__builtins__",
    "__import__",
    "breakpoint",
    "compile",
    "delattr",
    "dir",
    "eval",
    "exec",
    "getattr",
    "globals",
    "help",
    "input",
    "locals",
    "open",
    "setattr",
    "vars",
}


@dataclass(frozen=True)
class PythonToolResult:
    """Result returned by the restricted Python runner."""

    ok: bool
    stdout: str
    stderr: str
    returncode: int | None
    error: str = ""
    timeout: bool = False

    def render(self) -> str:
        """Render a concise model-visible observation."""
        parts = ["run_python result:"]
        if self.timeout:
            parts.append("status: timeout")
        elif self.ok:
            parts.append("status: ok")
        else:
            parts.append("status: failed")
        if self.returncode is not None:
            parts.append(f"returncode: {self.returncode}")
        if self.error:
            parts.append(f"error: {self.error}")
        if self.stdout:
            parts.extend(["stdout:", self.stdout])
        if self.stderr:
            parts.extend(["stderr:", self.stderr])
        if not self.stdout and not self.stderr and not self.error:
            parts.append("No output.")
        return "\n".join(parts)


class RestrictedPythonTool:
    """Run small self-contained Python calculations with guardrails."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        tool_config = config.get("tools", {}).get("python", {})
        qa_config = config.get("qa", {})
        self.timeout_seconds = float(
            tool_config.get("timeout_seconds", qa_config.get("python_timeout_seconds", 5))
        )
        self.max_output_chars = int(
            tool_config.get("max_output_chars", qa_config.get("python_max_output_chars", 8000))
        )

    def run(self, code: str) -> PythonToolResult:
        """Validate and execute code in a restricted subprocess."""
        code = str(code or "").strip()
        if not code:
            return PythonToolResult(
                ok=False,
                stdout="",
                stderr="",
                returncode=None,
                error="empty code",
            )
        try:
            _validate_code(code)
        except ValueError as exc:
            return PythonToolResult(
                ok=False,
                stdout="",
                stderr="",
                returncode=None,
                error=str(exc),
            )

        with tempfile.TemporaryDirectory(prefix="reviewer-python-tool-") as tmpdir:
            runner_path = Path(tmpdir) / "runner.py"
            runner_path.write_text(_runner_source(code), encoding="utf-8")
            try:
                completed = subprocess.run(
                    [sys.executable, "-I", str(runner_path)],
                    cwd=tmpdir,
                    env={},
                    text=True,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                return PythonToolResult(
                    ok=False,
                    stdout=_truncate(exc.stdout or "", self.max_output_chars),
                    stderr=_truncate(exc.stderr or "", self.max_output_chars),
                    returncode=None,
                    error=f"execution exceeded {self.timeout_seconds:g}s",
                    timeout=True,
                )
        return PythonToolResult(
            ok=completed.returncode == 0,
            stdout=_truncate(completed.stdout, self.max_output_chars),
            stderr=_truncate(completed.stderr, self.max_output_chars),
            returncode=completed.returncode,
        )


def _validate_code(code: str) -> None:
    """Reject code that tries to use filesystem, shell, network, or introspection."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise ValueError(f"syntax error: {exc}") from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_name = alias.name.split(".", 1)[0]
                if root_name not in ALLOWED_IMPORTS:
                    raise ValueError(f"forbidden import {alias.name!r}")
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                raise ValueError("relative imports are forbidden")
            root_name = node.module.split(".", 1)[0]
            if root_name not in ALLOWED_IMPORTS:
                raise ValueError(f"forbidden import {node.module!r}")
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_NAMES:
                raise ValueError(f"forbidden name {node.id!r}")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                raise ValueError(f"dunder attribute access is forbidden: {node.attr}")


def _runner_source(code: str) -> str:
    """Build the isolated runner script."""
    encoded_code = json.dumps(code)
    allowed_imports = json.dumps(sorted(ALLOWED_IMPORTS))
    return textwrap.dedent(
        f"""
        import builtins as _builtins
        import importlib as _importlib

        _ALLOWED_IMPORTS = set({allowed_imports})
        _PRELOADED = {{name: _importlib.import_module(name) for name in _ALLOWED_IMPORTS}}

        def _limited_import(name, globals=None, locals=None, fromlist=(), level=0):
            if level:
                raise ImportError("relative imports are disabled")
            root = name.split(".", 1)[0]
            if root not in _ALLOWED_IMPORTS:
                raise ImportError(f"import {{name!r}} is disabled")
            return _PRELOADED[root] if not fromlist else _importlib.import_module(name)

        _SAFE_BUILTINS = {{
            "ArithmeticError": ArithmeticError,
            "AssertionError": AssertionError,
            "Exception": Exception,
            "False": False,
            "IndexError": IndexError,
            "KeyError": KeyError,
            "None": None,
            "True": True,
            "TypeError": TypeError,
            "ValueError": ValueError,
            "__import__": _limited_import,
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "format": format,
            "int": int,
            "isinstance": isinstance,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "pow": pow,
            "print": print,
            "range": range,
            "repr": repr,
            "reversed": reversed,
            "round": round,
            "set": set,
            "slice": slice,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "zip": zip,
        }}

        _GLOBALS = {{"__builtins__": _SAFE_BUILTINS}}
        exec(compile({encoded_code}, "<run_python>", "exec"), _GLOBALS, _GLOBALS)
        """
    ).lstrip()


def _truncate(text: str, max_chars: int) -> str:
    text = str(text or "")
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n...[truncated]...\n" + text[-half:]

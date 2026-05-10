"""Purpose: Prompt loading helpers for agents and tools."""

from __future__ import annotations

from pathlib import Path


def get_repo_root(config: dict | None = None, start: str | Path | None = None) -> Path:
    """Resolve the repository root for prompt loading.

    Config-loaded workflows store `_repo_root`. For direct tests or scripts, walk
    upward from `start` or the current working directory until `config.yaml` is
    found.
    """
    if config and config.get("_repo_root"):
        return Path(str(config["_repo_root"]))

    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / "config.yaml").exists():
            return candidate
    return current


def load_prompt(path: str | Path, *, config: dict | None = None) -> str:
    """Load one UTF-8 prompt file.

    Relative paths are resolved from the repo root, so callers can use stable
    paths such as `prompts/summary_system.md`.
    """
    prompt_path = Path(path)
    if not prompt_path.is_absolute():
        prompt_path = get_repo_root(config) / prompt_path
    return prompt_path.read_text(encoding="utf-8")


def load_prompts(paths: list[str | Path], *, config: dict | None = None) -> list[str]:
    """Load multiple prompt files while preserving order."""
    return [load_prompt(path, config=config) for path in paths]


def join_prompts(paths: list[str | Path], *, config: dict | None = None) -> str:
    """Load and join multiple prompt files with blank lines."""
    return "\n\n".join(load_prompts(paths, config=config))

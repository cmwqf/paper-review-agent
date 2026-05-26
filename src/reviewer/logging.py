"""Purpose: Centralize logging setup for CLI, scripts, and workflows."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(config: dict | None = None, level: str | None = None) -> None:
    """Configure file logging, falling back to console only without a log file.

    Warnings from modules such as `reviewer.models.llm_client` flow through this
    logging setup. If `config['logging']['log_file']` is set, logs are written
    only to that file so long batch runs do not spam stderr.
    """
    logging_config = config.get("logging", {}) if isinstance(config, dict) else {}
    resolved_level = level or logging_config.get("level", "INFO")
    numeric_level = getattr(logging, str(resolved_level).upper(), logging.INFO)

    handlers: list[logging.Handler] = []
    log_file = logging_config.get("log_file")
    if log_file:
        log_path = Path(str(log_file))
        if not log_path.is_absolute() and config and config.get("_repo_root"):
            log_path = Path(str(config["_repo_root"])) / log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    else:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )

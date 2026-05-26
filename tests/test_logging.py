"""Purpose: Tests for central logging setup."""

from __future__ import annotations

import logging

from reviewer.logging import configure_logging


def test_configure_logging_writes_file(tmp_path) -> None:
    """Configured log files should receive module warnings."""
    log_file = tmp_path / "reviewer.log"
    configure_logging({"logging": {"level": "INFO", "log_file": str(log_file)}})
    logging.getLogger("reviewer.models.llm_client").warning("test warning")

    assert "test warning" in log_file.read_text(encoding="utf-8")


def test_configure_logging_uses_only_file_handler_when_log_file_is_set(tmp_path) -> None:
    """Configured log files should avoid console stream handlers."""
    log_file = tmp_path / "reviewer.log"
    configure_logging({"logging": {"level": "INFO", "log_file": str(log_file)}})

    assert [type(handler) for handler in logging.getLogger().handlers] == [logging.FileHandler]

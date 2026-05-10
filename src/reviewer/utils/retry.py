"""Purpose: Retry helpers for model and retrieval API calls."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def call_with_retries(fn: Callable[[], T], attempts: int = 3) -> T:
    """Call a zero-argument function with simple retry behavior."""
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as exc:  # pragma: no cover - placeholder behavior
            last_error = exc
    assert last_error is not None
    raise last_error


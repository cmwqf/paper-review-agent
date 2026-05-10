"""Purpose: Tests for config loading, environment expansion, and proxy resolution."""

from __future__ import annotations

from reviewer.settings import expand_env_vars, resolve_no_proxy


def test_expand_env_vars(monkeypatch) -> None:
    """`${VAR}` placeholders should expand recursively."""
    monkeypatch.setenv("REVIEWER_TEST_URL", "http://localhost:8000/v1")
    data = expand_env_vars({"models": [{"base_url": "${REVIEWER_TEST_URL}"}]})
    assert data["models"][0]["base_url"] == "http://localhost:8000/v1"


def test_model_no_proxy_takes_precedence() -> None:
    """Model-level no_proxy should override global no_proxy values."""
    config = {
        "network": {
            "no_proxy": "global.local",
            "default_no_proxy": ["localhost"],
        }
    }
    model_config = {"no_proxy": ["127.0.0.1"]}
    assert resolve_no_proxy(config, model_config) == "127.0.0.1"

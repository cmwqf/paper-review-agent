"""Purpose: Tests for config loading, environment expansion, and proxy resolution."""

from __future__ import annotations

from reviewer.settings import expand_env_vars, get_model_config, resolve_no_proxy


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


def test_get_model_config_inherits_default_values() -> None:
    """Model configs should inherit unset values from models.default."""
    config = {
        "models": {
            "default": {
                "model": "default-model",
                "base_url": "http://localhost:8000/v1",
                "api_key_env": "DEFAULT_KEY",
                "temperature": 0.2,
            },
            "agent": {"temperature": 0.3},
        }
    }

    model_config = get_model_config(config, "agent")

    assert model_config["model"] == "default-model"
    assert model_config["base_url"] == "http://localhost:8000/v1"
    assert model_config["api_key_env"] == "DEFAULT_KEY"
    assert model_config["temperature"] == 0.3


def test_get_model_config_applies_active_profile_overrides() -> None:
    """Active profiles should override defaults and role-level model configs."""
    config = {
        "models": {
            "active_profile": "deepseek_v4_pro",
            "default": {
                "model": "default-model",
                "base_url": "http://localhost:8000/v1",
                "api_key_env": "DEFAULT_KEY",
                "temperature": 0.2,
            },
            "final_review": {"temperature": 0.1},
            "profiles": {
                "deepseek_v4_pro": {
                    "final_review": {
                        "model": "deepseek-v4-pro",
                        "base_url": "https://api.deepseek.example/v1",
                        "api_key_env": "DEEPSEEK_API_KEY",
                    }
                }
            },
        }
    }

    model_config = get_model_config(config, "final_review")

    assert model_config["model"] == "deepseek-v4-pro"
    assert model_config["base_url"] == "https://api.deepseek.example/v1"
    assert model_config["api_key_env"] == "DEEPSEEK_API_KEY"
    assert model_config["temperature"] == 0.1


def test_runtime_model_profile_overrides_config_active_profile() -> None:
    """Runtime profile selection should take precedence over config defaults."""
    config = {
        "model_profile": "runtime_profile",
        "models": {
            "active_profile": "config_profile",
            "default": {
                "model": "default-model",
                "base_url": "http://localhost:8000/v1",
            },
            "final_review": {},
            "profiles": {
                "config_profile": {
                    "final_review": {"model": "config-model"},
                },
                "runtime_profile": {
                    "final_review": {"model": "runtime-model"},
                },
            },
        },
    }

    model_config = get_model_config(config, "final_review")

    assert model_config["model"] == "runtime-model"

"""Purpose: Load config.yaml and expose typed settings to the application."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


class ConfigError(ValueError):
    """Raised when the project configuration is incomplete or invalid."""


def load_env_file(path: str | Path, *, override: bool = False) -> None:
    """Load simple KEY=VALUE lines from a .env file into the process env.

    This intentionally avoids a dependency on python-dotenv. It supports the
    simple format used by this project and ignores comments and blank lines.
    """
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and (override or key not in os.environ):
            os.environ[key] = value


def expand_env_vars(value: Any) -> Any:
    """Recursively expand `${VAR}` placeholders in loaded YAML data.

    Missing environment variables expand to an empty string. Required values are
    checked later by the code that consumes the config.
    """
    if isinstance(value, dict):
        return {key: expand_env_vars(item) for key, item in value.items()}
    if isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), ""), value)
    return value


def load_config(path: str | Path, *, expand_env: bool = True) -> dict[str, Any]:
    """Load the single YAML config file used by the repo."""
    config_path = Path(path)
    load_env_file(config_path.resolve().parent / ".env")
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    data = expand_env_vars(data) if expand_env else data
    data["_config_path"] = str(config_path)
    data["_repo_root"] = str(config_path.resolve().parent)
    return data


def get_model_config(config: dict[str, Any], model_key: str) -> dict[str, Any]:
    """Return one model config and fail loudly if it is missing."""
    models = config.get("models")
    if not isinstance(models, dict):
        raise ConfigError("config.yaml must contain a 'models' mapping.")
    model_config = models.get(model_key)
    if not isinstance(model_config, dict):
        raise ConfigError(f"Model config not found: models.{model_key}")
    return model_config


def resolve_api_key(model_config: dict[str, Any]) -> str | None:
    """Resolve an API key from a model config's `api_key` or `api_key_env`."""
    explicit_key = model_config.get("api_key")
    if explicit_key:
        return str(explicit_key)

    env_name = model_config.get("api_key_env")
    if not env_name:
        return None
    api_key = os.getenv(str(env_name))
    if not api_key:
        raise ConfigError(f"Environment variable is required but unset: {env_name}")
    return api_key


def _as_list(value: Any) -> list[str]:
    """Normalize scalar or list config values into a list of non-empty strings."""
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def resolve_no_proxy(config: dict[str, Any], model_config: dict[str, Any]) -> str | None:
    """Resolve NO_PROXY for a model, with model-level values taking precedence.

    If a model defines `no_proxy`, it is used directly. Otherwise the global
    `network.no_proxy`, `network.default_no_proxy`, and environment `NO_PROXY`
    are merged.
    """
    if "no_proxy" in model_config:
        values = _as_list(model_config.get("no_proxy"))
    else:
        network = config.get("network", {}) if isinstance(config.get("network"), dict) else {}
        values = []
        values.extend(_as_list(network.get("no_proxy")))
        values.extend(_as_list(network.get("default_no_proxy")))
        values.extend(_as_list(os.getenv("NO_PROXY")))

    deduped = list(dict.fromkeys(values))
    return ",".join(deduped) if deduped else None


def resolve_all_proxy(config: dict[str, Any], model_config: dict[str, Any]) -> str | None:
    """Resolve ALL_PROXY for a model.

    Model-level `all_proxy` overrides global `network.all_proxy`; both may come
    from environment-expanded config values.
    """
    if "all_proxy" in model_config:
        value = model_config.get("all_proxy")
    else:
        network = config.get("network", {}) if isinstance(config.get("network"), dict) else {}
        value = network.get("all_proxy") or os.getenv("ALL_PROXY")
    return str(value) if value else None

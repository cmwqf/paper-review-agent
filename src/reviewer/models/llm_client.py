"""Purpose: LLM client implementation for summary, agent, answer, and final models."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

import requests

from reviewer.settings import ConfigError, resolve_all_proxy, resolve_api_key, resolve_no_proxy

LOGGER = logging.getLogger(__name__)


def resolve_chat_endpoint(base_url: str) -> str:
    """Resolve a model base URL to a chat-completions endpoint.

    If the configured URL already points to a `chat/completions` or `messages`
    endpoint, it is used as-is. Otherwise `/chat/completions` is appended.
    """
    cleaned = base_url.rstrip("/")
    if "chat/completions" in cleaned or "messages" in cleaned:
        return cleaned
    return f"{cleaned}/chat/completions"


def is_gpt_model(model_name: str) -> bool:
    """Return whether a model name appears to be a GPT-family model."""
    parts = re.split(r"[/:\s]+", model_name.lower())
    return any(part.startswith("gpt") for part in parts)


@dataclass
class LLMClient:
    """OpenAI-compatible chat completion client.

    The same client is intended to work with OpenRouter, OpenAI-compatible local
    vLLM servers, and other services that accept OpenAI-style chat payloads.
    """

    model_config: dict[str, Any]
    global_config: dict[str, Any] | None = None
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self) -> None:
        self.global_config = self.global_config or {}
        self.base_url = str(self.model_config.get("base_url") or "").strip()
        if not self.base_url:
            raise ConfigError("Model config must define base_url.")
        self.endpoint = resolve_chat_endpoint(self.base_url)
        self.model = str(self.model_config.get("model") or "").strip()
        if not self.model:
            raise ConfigError("Model config must define model.")
        self.api_key = resolve_api_key(self.model_config)

    def _headers(self) -> dict[str, str]:
        """Build HTTP headers for an OpenAI-compatible request."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _proxies(self) -> dict[str, str] | None:
        """Build per-request proxy settings, including model-specific NO_PROXY."""
        all_proxy = resolve_all_proxy(self.global_config, self.model_config)
        no_proxy = resolve_no_proxy(self.global_config, self.model_config)
        proxies: dict[str, str] = {}
        if all_proxy:
            proxies["http"] = all_proxy
            proxies["https"] = all_proxy
        if no_proxy:
            proxies["no_proxy"] = no_proxy
        return proxies or None

    def _payload(self, messages: list[dict[str, Any]], overrides: dict[str, Any]) -> dict[str, Any]:
        """Build a chat-completions payload from config plus call overrides."""
        model = str(overrides.pop("model", self.model))
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        gpt_model = is_gpt_model(model)

        token_value = overrides.pop("max_tokens", self.model_config.get("max_tokens"))
        explicit_completion_tokens = overrides.pop(
            "max_completion_tokens", self.model_config.get("max_completion_tokens")
        )
        if explicit_completion_tokens is not None:
            payload["max_completion_tokens"] = explicit_completion_tokens
        elif token_value is not None:
            if gpt_model:
                payload["max_completion_tokens"] = token_value
                LOGGER.warning(
                    "Detected GPT model '%s'; mapping config max_tokens to max_completion_tokens.",
                    model,
                )
            else:
                payload["max_tokens"] = token_value

        temperature = overrides.pop("temperature", self.model_config.get("temperature"))
        if gpt_model:
            if temperature != 1:
                LOGGER.warning(
                    "Detected GPT model '%s'; overriding temperature=%r to temperature=1.",
                    model,
                    temperature,
                )
            payload["temperature"] = 1
        elif temperature is not None:
            payload["temperature"] = temperature

        for key in (
            "top_p",
            "presence_penalty",
            "frequency_penalty",
            "stop",
            "response_format",
        ):
            value = overrides.pop(key, self.model_config.get(key))
            if value is not None:
                payload[key] = value
        payload.update(overrides)
        return payload

    def _extract_text(self, data: dict[str, Any]) -> str:
        """Extract assistant text from common OpenAI-compatible responses."""
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict) and message.get("content") is not None:
                    content = message["content"]
                    if isinstance(content, str):
                        return content
                    if isinstance(content, list):
                        text_parts = [
                            str(item.get("text"))
                            for item in content
                            if isinstance(item, dict) and item.get("text") is not None
                        ]
                        return "".join(text_parts)
                    return str(content)
                if first.get("text") is not None:
                    return str(first["text"])

        content = data.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = [
                str(item.get("text"))
                for item in content
                if isinstance(item, dict) and item.get("text") is not None
            ]
            if text_parts:
                return "".join(text_parts)

        raise RuntimeError(f"Unable to extract text from model response: {data}")

    def _response_debug(self, data: dict[str, Any]) -> dict[str, Any]:
        """Return compact response metadata useful for diagnosing empty outputs."""
        debug: dict[str, Any] = {}
        for key in ("id", "model", "object", "created", "usage"):
            if key in data:
                debug[key] = data[key]
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                debug["finish_reason"] = first.get("finish_reason")
                message = first.get("message")
                if isinstance(message, dict):
                    debug["message_keys"] = sorted(message.keys())
                    if message.get("refusal"):
                        debug["refusal"] = message.get("refusal")
                    if message.get("reasoning"):
                        debug["reasoning_present"] = True
        return debug

    def generate(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        """Call the configured model and return the assistant text."""
        timeout = float(kwargs.pop("timeout_seconds", self.model_config.get("timeout_seconds", 60)))
        max_retries = int(kwargs.pop("max_retries", self.model_config.get("max_retries", 3)))
        payload = self._payload(messages, kwargs)

        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                response = self.session.post(
                    self.endpoint,
                    headers=self._headers(),
                    json=payload,
                    timeout=timeout,
                    proxies=self._proxies(),
                )
                try:
                    response.raise_for_status()
                except Exception:
                    LOGGER.error(
                        "Model HTTP error on attempt %s/%s: model=%s endpoint=%s status=%s body=%s",
                        attempt,
                        max_retries,
                        self.model,
                        self.endpoint,
                        getattr(response, "status_code", "unknown"),
                        getattr(response, "text", ""),
                    )
                    raise
                try:
                    data = response.json()
                except Exception:
                    LOGGER.error(
                        "Model response JSON parse failed on attempt %s/%s: model=%s endpoint=%s body=%s",
                        attempt,
                        max_retries,
                        self.model,
                        self.endpoint,
                        getattr(response, "text", ""),
                    )
                    raise
                LOGGER.info(
                    "Model raw response on attempt %s/%s: model=%s endpoint=%s raw_response=%r",
                    attempt,
                    max_retries,
                    self.model,
                    self.endpoint,
                    data,
                )
                try:
                    output = self._extract_text(data)
                except Exception:
                    LOGGER.error(
                        "Unable to extract text from model response on attempt %s/%s: model=%s endpoint=%s raw_response=%r",
                        attempt,
                        max_retries,
                        self.model,
                        self.endpoint,
                        data,
                    )
                    raise
                if not output.strip():
                    LOGGER.error(
                        "Model returned empty assistant content on attempt %s/%s: model=%s endpoint=%s raw_response=%r",
                        attempt,
                        max_retries,
                        self.model,
                        self.endpoint,
                        data,
                    )
                    raise RuntimeError(f"Model returned empty assistant content: {self._response_debug(data)}")
                return output
            except Exception as exc:
                LOGGER.warning(
                    "Model call attempt %s/%s failed: model=%s endpoint=%s error=%r",
                    attempt,
                    max_retries,
                    self.model,
                    self.endpoint,
                    exc,
                )
                last_error = exc
        assert last_error is not None
        raise last_error

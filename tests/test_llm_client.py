"""Purpose: Tests for the OpenAI-compatible LLM client without network calls."""

from __future__ import annotations

from reviewer.models.llm_client import LLMClient, is_gpt_model, resolve_chat_endpoint


class FakeResponse:
    """Small fake response object for testing response parsing."""

    def raise_for_status(self) -> None:
        """Pretend the HTTP request succeeded."""

    def json(self) -> dict:
        """Return an OpenAI-style response body."""
        return {"choices": [{"message": {"content": "<xml>ok</xml>"}}]}


class FakeSession:
    """Capture the outgoing request without performing network I/O."""

    def __init__(self) -> None:
        self.request = None

    def post(self, url, **kwargs):
        """Store request kwargs and return a fake response."""
        self.request = kwargs
        self.request["url"] = url
        return FakeResponse()


def test_resolve_chat_endpoint_appends_chat_completions() -> None:
    """Root base URLs should become chat-completions endpoints."""
    assert (
        resolve_chat_endpoint("http://localhost:8000/v1")
        == "http://localhost:8000/v1/chat/completions"
    )


def test_resolve_chat_endpoint_keeps_full_endpoint() -> None:
    """Already complete endpoints should not be modified."""
    assert (
        resolve_chat_endpoint("http://localhost:8000/v1/chat/completions")
        == "http://localhost:8000/v1/chat/completions"
    )


def test_is_gpt_model_detects_provider_prefixed_names() -> None:
    """OpenRouter-style provider prefixes should still detect GPT models."""
    assert is_gpt_model("openai/gpt-5.5")
    assert is_gpt_model("gpt-4o")
    assert not is_gpt_model("meta-llama/llama-3.1-70b")


def test_llm_client_generates_openai_payload() -> None:
    """LLMClient should send model config and return assistant content."""
    session = FakeSession()
    client = LLMClient(
        {
            "model": "local-model",
            "base_url": "http://localhost:8000/v1",
            "api_key_env": None,
            "temperature": 0.2,
            "max_tokens": 128,
            "no_proxy": ["localhost"],
        },
        global_config={"network": {"all_proxy": "socks5://127.0.0.1:7890"}},
        session=session,
    )
    output = client.generate([{"role": "user", "content": "hello"}])

    assert output == "<xml>ok</xml>"
    assert session.request["json"]["model"] == "local-model"
    assert session.request["json"]["temperature"] == 0.2
    assert session.request["json"]["max_tokens"] == 128
    assert session.request["proxies"]["no_proxy"] == "localhost"


def test_llm_client_maps_gpt_max_tokens_and_temperature(caplog) -> None:
    """GPT models should use max_completion_tokens and temperature=1."""
    session = FakeSession()
    client = LLMClient(
        {
            "model": "openai/gpt-5.5",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key_env": None,
            "temperature": 0.2,
            "max_tokens": 4096,
        },
        session=session,
    )
    output = client.generate([{"role": "user", "content": "hello"}])

    assert output == "<xml>ok</xml>"
    assert session.request["json"]["max_completion_tokens"] == 4096
    assert "max_tokens" not in session.request["json"]
    assert session.request["json"]["temperature"] == 1
    assert "Detected GPT model" in caplog.text

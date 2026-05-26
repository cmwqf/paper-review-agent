"""Purpose: Tests for the OpenAI-compatible LLM client without network calls."""

from __future__ import annotations

from reviewer.models.llm_client import LLMClient, is_gpt_model, resolve_chat_endpoint


class FakeResponse:
    """Small fake response object for testing response parsing."""

    def __init__(self, data=None) -> None:
        self.data = data or {"choices": [{"message": {"content": "<xml>ok</xml>"}}]}

    def raise_for_status(self) -> None:
        """Pretend the HTTP request succeeded."""

    def json(self) -> dict:
        """Return an OpenAI-style response body."""
        return self.data


class FakeSession:
    """Capture the outgoing request without performing network I/O."""

    def __init__(self, responses=None) -> None:
        self.request = None
        self.responses = list(responses or [FakeResponse()])
        self.calls = 0

    def post(self, url, **kwargs):
        """Store request kwargs and return a fake response."""
        self.request = kwargs
        self.request["url"] = url
        self.calls += 1
        if len(self.responses) > 1:
            return self.responses.pop(0)
        return self.responses[0]


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


def test_llm_client_retries_empty_model_content() -> None:
    """Empty assistant content should be treated as a retryable model failure."""
    session = FakeSession(
        [
            FakeResponse(
                {
                    "choices": [
                        {
                            "message": {"content": ""},
                            "finish_reason": "length",
                        }
                    ],
                    "usage": {"completion_tokens": 128},
                }
            ),
            FakeResponse({"choices": [{"message": {"content": "<xml>ok</xml>"}}]}),
        ]
    )
    client = LLMClient(
        {
            "model": "local-model",
            "base_url": "http://localhost:8000/v1",
            "api_key_env": None,
            "max_retries": 2,
        },
        session=session,
    )

    assert client.generate([{"role": "user", "content": "hello"}]) == "<xml>ok</xml>"
    assert session.calls == 2


def test_llm_client_logs_raw_empty_response(caplog) -> None:
    """Raw model JSON should be logged when assistant content is empty."""
    session = FakeSession(
        [
            FakeResponse(
                {
                    "choices": [
                        {
                            "message": {"content": ""},
                            "finish_reason": "length",
                        }
                    ],
                    "usage": {"completion_tokens": 128},
                }
            )
        ]
    )
    client = LLMClient(
        {
            "model": "local-model",
            "base_url": "http://localhost:8000/v1",
            "api_key_env": None,
            "max_retries": 1,
        },
        session=session,
    )

    try:
        client.generate([{"role": "user", "content": "hello"}])
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected empty model content to fail.")

    assert "raw_response=" in caplog.text
    assert "finish_reason" in caplog.text
    assert "completion_tokens" in caplog.text


def test_llm_client_logs_raw_success_response(caplog) -> None:
    """Successful model responses should also be logged for debugging."""
    caplog.set_level("INFO")
    session = FakeSession(
        [
            FakeResponse(
                {
                    "id": "chatcmpl-ok",
                    "choices": [{"message": {"content": "<xml>ok</xml>"}}],
                }
            )
        ]
    )
    client = LLMClient(
        {
            "model": "local-model",
            "base_url": "http://localhost:8000/v1",
            "api_key_env": None,
        },
        session=session,
    )

    assert client.generate([{"role": "user", "content": "hello"}]) == "<xml>ok</xml>"
    assert "Model raw response" in caplog.text
    assert "chatcmpl-ok" in caplog.text

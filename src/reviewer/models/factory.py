"""Purpose: Construct model clients from the single config.yaml."""

from __future__ import annotations

from reviewer.models.llm_client import LLMClient
from reviewer.models.reranker_client import RerankerClient
from reviewer.models.vlm_client import VLMClient
from reviewer.settings import get_model_config


def build_llm(config: dict, model_key: str) -> LLMClient:
    """Build an LLM client by key from config['models']."""
    return LLMClient(get_model_config(config, model_key), global_config=config)


def build_vlm(config: dict, model_key: str) -> VLMClient:
    """Build a VLM client by key from config['models']."""
    return VLMClient(get_model_config(config, model_key), global_config=config)


def build_reranker(config: dict, model_key: str) -> RerankerClient:
    """Build a reranker client by key from config['models']."""
    return RerankerClient(get_model_config(config, model_key), global_config=config)

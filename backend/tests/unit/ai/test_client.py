"""Tests for AI client infrastructure."""

from __future__ import annotations

import pytest

from pdf_modifier.ai.client import NaNClient, NullAIClient


class TestNullAIClient:
    """NullAIClient for deterministic testing."""

    @pytest.mark.asyncio
    async def test_chat_returns_mock_response(self) -> None:
        client = NullAIClient()
        result = await client.chat("mimo-v2.5", [{"role": "user", "content": "test"}])
        assert "choices" in result
        assert len(result["choices"]) > 0
        assert client.call_count == 1

    @pytest.mark.asyncio
    async def test_embed_returns_mock_embedding(self) -> None:
        client = NullAIClient()
        result = await client.embed("qwen3-embedding", "test text")
        assert "data" in result
        assert len(result["data"]) > 0
        assert client.call_count == 1

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        async with NullAIClient() as client:
            result = await client.chat("mimo-v2.5", [{"role": "user", "content": "test"}])
            assert result is not None

    def test_is_configured(self) -> None:
        client = NullAIClient()
        assert client.is_configured is True


class TestNaNClientConfig:
    """NaNClient configuration."""

    def test_default_base_url(self) -> None:
        client = NaNClient(api_key="test-key")
        assert client._base_url == "https://api.nan.builders/v1"

    def test_custom_base_url(self) -> None:
        client = NaNClient(api_key="test-key", base_url="https://custom.api/v1")
        assert client._base_url == "https://custom.api/v1"

    def test_is_configured_with_key(self) -> None:
        client = NaNClient(api_key="test-key")
        assert client.is_configured is True

    def test_not_configured_without_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("NAN_API_KEY", raising=False)
        client = NaNClient()
        assert client.is_configured is False

    def test_env_var_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NAN_API_KEY", "env-key")
        client = NaNClient()
        assert client.is_configured is True

    def test_explicit_key_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NAN_API_KEY", "env-key")
        client = NaNClient(api_key="explicit-key")
        # The explicit key should be used
        assert client._api_key == "explicit-key"

    def test_env_var_base_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NAN_BASE_URL", "https://env.api/v1")
        client = NaNClient(api_key="test")
        assert client._base_url == "https://env.api/v1"

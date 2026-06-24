"""Tests for model router."""

from __future__ import annotations

import pytest

from pdf_modifier.ai.router import ModelRouter, TaskType


class TestModelRouter:
    """Model routing tests."""

    def test_default_vision_model(self) -> None:
        router = ModelRouter()
        assert router.get_model(TaskType.VISION) == "mimo-v2.5"

    def test_default_classification_model(self) -> None:
        router = ModelRouter()
        assert router.get_model(TaskType.CLASSIFICATION) == "qwen3.6"

    def test_default_embedding_model(self) -> None:
        router = ModelRouter()
        assert router.get_model(TaskType.EMBEDDING) == "qwen3-embedding"

    def test_all_task_types_have_models(self) -> None:
        router = ModelRouter()
        for task_type in TaskType:
            model = router.get_model(task_type)
            assert isinstance(model, str)
            assert len(model) > 0

    def test_override_model(self) -> None:
        router = ModelRouter()
        router.set_model(TaskType.VISION, "custom-model")
        assert router.get_model(TaskType.VISION) == "custom-model"

    def test_fallback_chain(self) -> None:
        router = ModelRouter()
        chain = router.get_fallback_chain()
        assert chain == ["mimo-v2.5", "qwen3.6", "gemma4"]

    def test_custom_routing(self) -> None:
        custom = {TaskType.VISION: "custom-vision"}
        router = ModelRouter(routing=custom)
        assert router.get_model(TaskType.VISION) == "custom-vision"
        # Other types should still use defaults
        assert router.get_model(TaskType.CLASSIFICATION) == "qwen3.6"

    def test_get_model_raises_for_missing(self) -> None:
        """Raising ValueError when no model configured for a task type."""
        # Pass None to use defaults, then remove the VISION entry
        router = ModelRouter()
        del router._routing[TaskType.VISION]
        with pytest.raises(ValueError, match="No model configured"):
            router.get_model(TaskType.VISION)

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AI_MODEL_VISION", "override-model")
        router = ModelRouter()
        assert router.get_model(TaskType.VISION) == "override-model"

    def test_env_override_classification(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AI_MODEL_CLASSIFICATION", "fast-model")
        router = ModelRouter()
        assert router.get_model(TaskType.CLASSIFICATION) == "fast-model"

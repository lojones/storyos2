"""Tests for utils.visualization_utils."""

import pytest

from models.visualization_response import VisualizationResponse
from utils.visualization_utils import VisualizationManager


class _StubKlingClient:
    """Test double for KlingClient."""

    def __init__(self):
        self.calls = []

    def generate_image_from_prompt(self, prompt):
        self.calls.append(prompt)
        return VisualizationResponse(
            task_id="stub-task-id",
            image_url="https://example.com/image.png",
            content=b"fake-bytes",
            task_status="succeed",
        )


class TestVisualizationManagerIntegration:
    """Integration-style tests for VisualizationManager."""

    def test_submit_prompt_returns_response(self, monkeypatch):
        client = _StubKlingClient()

        def _factory():  # mimic KlingClient constructor
            return client

        monkeypatch.setattr("utils.visualization_utils.KlingClient", _factory)

        response = VisualizationManager.submit_prompt("  explore the ancient ruins ")

        assert isinstance(response, VisualizationResponse)
        assert response.task_id == "stub-task-id"
        assert client.calls == ["explore the ancient ruins"]

    def test_submit_prompt_missing_task_id_raises(self, monkeypatch):
        class _BadClient:
            def generate_image_from_prompt(self, prompt):
                return {}

        monkeypatch.setattr("utils.visualization_utils.KlingClient", _BadClient)

        with pytest.raises(ValueError):
            VisualizationManager.submit_prompt("summon a dragon")

    def test_submit_prompt_rejects_empty_prompt(self):
        with pytest.raises(ValueError):
            VisualizationManager.submit_prompt("  ")

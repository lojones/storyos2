"""Visualization utilities for StoryOS."""

from __future__ import annotations

from typing import Dict

from logging_config import get_logger
from utils.kling_client import KlingClient


class VisualizationManager:
    """High-level helper for creating visualization tasks."""

    _logger = get_logger("visualization_utils")

    @staticmethod
    def submit_prompt(prompt: str) -> str:
        """Submit an image prompt and return the Kling task identifier."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt is required for visualization requests.")

        cleaned_prompt = prompt.strip()
        VisualizationManager._logger.debug(
            "Submitting visualization prompt (length=%s)", len(cleaned_prompt)
        )

        client = KlingClient()
        response: Dict[str, object] = client.generate_image_from_prompt(cleaned_prompt)

        task_id_obj = response.get("task_id")
        if not isinstance(task_id_obj, str):
            VisualizationManager._logger.error("Kling response missing task_id: %s", response)
            raise ValueError("Kling.ai response did not include a task_id.")

        VisualizationManager._logger.info("Visualization task created (task_id=%s)", task_id_obj)
        return task_id_obj

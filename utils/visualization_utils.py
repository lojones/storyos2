"""Visualization utilities for StoryOS."""

from __future__ import annotations

from logging_config import get_logger
from utils.kling_client import KlingClient
from models.visualization_response import VisualizationResponse


class VisualizationManager:
    """High-level helper for creating visualization tasks."""

    _logger = get_logger("visualization_utils")

    @staticmethod
    def submit_prompt(prompt: str) -> VisualizationResponse:
        """Submit an image prompt and return the Kling response payload."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt is required for visualization requests.")

        cleaned_prompt = prompt.strip()
        VisualizationManager._logger.debug(
            "Submitting visualization prompt (length=%s)", len(cleaned_prompt)
        )

        client = KlingClient()
        response_obj: object = client.generate_image_from_prompt(cleaned_prompt)

        if not isinstance(response_obj, VisualizationResponse):
            VisualizationManager._logger.error(
                "Unexpected response type from KlingClient: %s", type(response_obj)
            )
            raise ValueError("Unexpected response type from Kling.ai client.")

        visualization_response = response_obj

        VisualizationManager._logger.info(
            "Visualization task created (task_id=%s)", visualization_response.task_id
        )
        return visualization_response

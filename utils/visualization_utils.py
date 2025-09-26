"""Visualization utilities for StoryOS."""

from __future__ import annotations

import time

from logging_config import StoryOSLogger, get_logger
from models.image_prompts import VisualPrompts
from models.visualization_response import VisualizationResponse
from utils.db_utils import get_db_manager
from utils.kling_client import KlingClient
from utils.llm_utils import get_llm_utility
from utils.model_utils import ModelUtils
from utils.prompts import PromptCreator


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

    @staticmethod
    def generate_prompts_for_session(session_id: str) -> None:
        """Generate visualization prompts for the latest chat message."""
        logger = VisualizationManager._logger
        start_time = time.time()

        logger.info("Generating visualization prompts for session: %s", session_id)

        try:
            db = get_db_manager()

            if not db.is_connected():
                logger.error("Database connection failed during visualization prompt generation")
                return

            session = db.get_game_session(session_id)
            if not session:
                logger.error("Game session not found: %s", session_id)
                return

            metaprompt = PromptCreator.build_visualization_prompt(session)
            if not metaprompt:
                logger.error("Failed to build visualization metaprompt")
                raise ValueError("Visualization metaprompt generation failed")

            llm = get_llm_utility()
            visual_prompts_str = llm.call_fast_llm_nostream(
                metaprompt,
                VisualPrompts.model_json_schema(),
                prompt_type="visualization-metaprompt",
            )
            visual_prompts_obj = ModelUtils.model_from_string(
                visual_prompts_str,
                VisualPrompts,
            )
            db.add_visual_prompts_to_latest_message(session_id, visual_prompts_obj)

        except Exception as exc:  # noqa: BLE001
            duration = time.time() - start_time
            logger.error(
                "Error generating visualization prompts for session %s: %s",
                session_id,
                exc,
            )
            StoryOSLogger.log_error_with_context(
                "visualization_utils",
                exc,
                {
                    "operation": "generate_visualization_prompts",
                    "session_id": session_id,
                    "duration": duration,
                },
            )

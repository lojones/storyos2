"""Grok-2-Image client utilities for StoryOS visualizations."""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Dict, Optional, cast

import requests
from requests import Response

from backend.logging_config import get_logger, StoryOSLogger
from backend.utils.db_utils import get_db_manager
from backend.utils.log_utils import write_json_log, append_json_log
from backend.models.visualization_response import VisualizationResponse


JsonDict = Dict[str, Any]


class GrokImageClient:
    """Client wrapper for interacting with the Grok-2-Image generation API."""

    GENERATION_ENDPOINT = "/v1/images/generations"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.logger = get_logger("grok2image_client")

        api_key_value = api_key or os.getenv("XAI_API_KEY")

        if not api_key_value:
            raise ValueError("XAI_API_KEY environment variable must be set.")

        self.api_key: str = api_key_value
        self.base_url = base_url or os.getenv("XAI_BASE_URL", "https://api.x.ai")
        self.model_name = model_name or os.getenv("XAI_IMAGE_MODEL_NAME", "grok-2-image")
        self.num_images = int(os.getenv("XAI_NUM_IMAGES", "1"))
        self.response_format = os.getenv("XAI_RESPONSE_FORMAT", "url")
        self.request_timeout = int(os.getenv("XAI_REQUEST_TIMEOUT", "120"))

        self.session = requests.Session()

        self.logger.debug(f"GrokImageClient initialized: base_url={self.base_url}, model={self.model_name}, "
                         f"num_images={self.num_images}, response_format={self.response_format}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_image_from_prompt(
        self,
        prompt: str,
        *,
        session_id: str,
        message_id: str
    ) -> VisualizationResponse:
        """Generate an image from a prompt using Grok-2-Image API.

        Unlike Kling.ai's async task model, Grok-2-Image returns the completed
        image URL directly in the response. This method adapts that synchronous
        model to match the VisualizationResponse interface.
        """
        if not prompt:
            raise ValueError("Prompt is required for Grok-2-Image generation.")

        # Truncate prompt at 1000 characters before making the API call
        truncated_prompt = prompt[:1000]

        db = get_db_manager()

        # Generate a pseudo task_id for consistency with Kling workflow
        # Format: grok2img_<timestamp>_<session_id[:8]>
        task_id = f"grok2img_{int(time.time())}_{session_id[:8]}"

        payload: JsonDict = {
            "model": self.model_name,
            "prompt": truncated_prompt,
            "n": self.num_images,
            "response_format": self.response_format,
        }

        headers = self._build_headers()
        generation_url = self._build_url(self.GENERATION_ENDPOINT)

        log_path = write_json_log({
            "url": generation_url,
            "headers": {"Authorization": "<redacted>", "Content-Type": headers.get("Content-Type")},
            "payload": payload,
        }, prefix="grok2image_request")

        self.logger.info("Submitting Grok-2-Image generation request")
        StoryOSLogger.log_user_action("system", "grok2image_submit", {
            "prompt_length": len(truncated_prompt),
            "model_name": self.model_name,
            "num_images": self.num_images,
        })

        # Persist task record as "submitted"
        task_created = db.create_visualization_task({
            "task_id": task_id,
            "session_id": session_id,
            "message_id": message_id,
            "prompt": truncated_prompt,
            "model_name": self.model_name,
            "task_status": "submitted",
            "task_status_msg": "Request submitted to Grok-2-Image API",
        })

        if not task_created:
            self.logger.warning("Visualization task %s could not be persisted", task_id)

        try:
            response: Response = self.session.post(
                generation_url,
                json=payload,
                headers=headers,
                timeout=self.request_timeout
            )

            # Log response regardless of status for debugging
            self.logger.debug(f"API response status: {response.status_code}")

            response.raise_for_status()
            response_data = cast(JsonDict, response.json())

            append_json_log(log_path, {
                "type": "generation_response",
                "status_code": response.status_code,
                "body": response_data,
            })

        except Exception as exc:
            response_obj = cast(Optional[Response], getattr(exc, "response", None))
            status_code: Optional[int] = getattr(response_obj, "status_code", None) if response_obj is not None else None
            error_msg = str(exc)
            error_body = None

            # Try to get the response body for more details
            if response_obj is not None:
                try:
                    error_body = response_obj.text
                except Exception:
                    pass

            self.logger.error(f"Grok-2-Image API error: {error_msg}")
            if error_body:
                self.logger.error(f"Response body: {error_body}")

            append_json_log(log_path, {
                "type": "generation_error",
                "error": error_msg,
                "status_code": status_code,
                "response_body": error_body,
            })

            # Update task as failed
            db.update_visualization_task(task_id, {
                "task_status": "failed",
                "task_status_msg": error_msg,
            })

            raise RuntimeError(f"Grok-2-Image generation failed: {error_msg}") from exc

        # Extract image URL from response
        image_url = self._extract_image_url(response_data)
        revised_prompt = self._extract_revised_prompt(response_data)

        self.logger.info(f"Grok-2-Image generation completed (task_id={task_id})")
        StoryOSLogger.log_user_action("system", "grok2image_completed", {
            "task_id": task_id,
            "image_url_present": bool(image_url),
            "revised_prompt_present": bool(revised_prompt),
        })

        # Update task as completed
        db.update_visualization_task(task_id, {
            "task_status": "succeed",
            "task_status_msg": "Image generated successfully",
            "image_url": image_url,
            "task_result": {
                "images": [{
                    "url": image_url,
                    "revised_prompt": revised_prompt,
                }]
            },
            "image_retrieved_at": datetime.utcnow().isoformat(),
        })

        append_json_log(log_path, {
            "type": "task_complete",
            "task_id": task_id,
            "image_url": image_url,
        })

        return VisualizationResponse(
            task_id=task_id,
            image_url=image_url,
            task_status="succeed",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    def _extract_image_url(self, response_data: JsonDict) -> str:
        """Extract image URL from Grok-2-Image API response.

        Expected response format:
        {
            "created": 1715888888,
            "data": [
                {
                    "url": "https://img.x.ai/generated-image-url/...",
                    "revised_prompt": "..."
                }
            ]
        }
        """
        data = response_data.get("data")
        if not isinstance(data, list) or not data:
            raise ValueError("Grok-2-Image response missing 'data' array or array is empty")

        first_item = data[0]
        if not isinstance(first_item, dict):
            raise ValueError("Grok-2-Image response data[0] is not a dictionary")

        # Handle both 'url' and 'b64_json' response formats
        if self.response_format == "url":
            image_url = first_item.get("url")
            if not isinstance(image_url, str) or not image_url:
                raise ValueError("Grok-2-Image response missing 'url' field")
            return image_url
        elif self.response_format == "b64_json":
            b64_data = first_item.get("b64_json")
            if not isinstance(b64_data, str) or not b64_data:
                raise ValueError("Grok-2-Image response missing 'b64_json' field")
            # For b64_json, return a data URL that can be used directly
            return f"data:image/png;base64,{b64_data}"
        else:
            raise ValueError(f"Unsupported response_format: {self.response_format}")

    def _extract_revised_prompt(self, response_data: JsonDict) -> Optional[str]:
        """Extract revised prompt if present in the response."""
        try:
            data = response_data.get("data")
            if isinstance(data, list) and data:
                first_item = data[0]
                if isinstance(first_item, dict):
                    return first_item.get("revised_prompt")
        except Exception:
            pass
        return None


__all__ = ["GrokImageClient"]

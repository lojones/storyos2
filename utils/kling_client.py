"""Kling.ai client utilities for StoryOS visualizations."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, Mapping, Optional, TypedDict, NotRequired, cast

import requests
from requests import Response

from logging_config import get_logger, StoryOSLogger
from utils.db_utils import get_db_manager
from utils.log_utils import write_json_log, append_json_log
from models.visualization_response import VisualizationResponse


JsonDict = Dict[str, Any]


class _KlingTaskResult(TypedDict, total=False):
    images: list[Dict[str, Any]]


class _KlingTaskData(TypedDict):
    task_id: str
    task_status: NotRequired[str]
    task_status_msg: NotRequired[str]
    task_result: NotRequired[_KlingTaskResult]


class KlingClient:
    """Client wrapper for interacting with the Kling.ai image generation API."""

    CREATE_TASK_PATH = "/v1/images/generations"
    QUERY_TASK_PATH_TEMPLATE = "/v1/images/generations/{task_id}"

    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.logger = get_logger("kling_client")

        access_key_value = access_key or os.getenv("KLING_ACCESS_KEY")
        secret_key_value = secret_key or os.getenv("KLING_SECRET_KEY")

        if not access_key_value or not secret_key_value:
            raise ValueError("KLING_ACCESS_KEY and KLING_SECRET_KEY environment variables must be set.")

        self.access_key: str = access_key_value
        self.secret_key: str = secret_key_value

        self.base_url = base_url or os.getenv("KLING_BASE_URL", "https://api-singapore.klingai.com")
        self.model_name = model_name or os.getenv("KLING_MODEL_NAME", "kling-v2")
        self.default_aspect_ratio = os.getenv("KLING_ASPECT_RATIO", "16:9")
        self.poll_interval = float(os.getenv("KLING_POLL_INTERVAL", "2.0"))
        self.poll_timeout = int(os.getenv("KLING_POLL_TIMEOUT", "180"))
        self.jwt_ttl = int(os.getenv("KLING_JWT_TTL", "1800"))

        self.session = requests.Session()
        self._cached_token: Optional[str] = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_image_from_prompt(
        self,
        prompt: str,
        *,
        session_id: Optional[str] = None,
        message_id: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
    ) -> VisualizationResponse:
        """Create a Kling.ai task, persist it, poll until completion, and return image bytes."""
        if not prompt:
            raise ValueError("Prompt is required for Kling.ai image generation.")

        db = get_db_manager()

        payload: JsonDict = {
            "model_name": self.model_name,
            "prompt": prompt,
        }
        ratio = aspect_ratio or self.default_aspect_ratio
        if ratio:
            payload["aspect_ratio"] = ratio

        headers = self._build_headers()
        create_url = self._build_url(self.CREATE_TASK_PATH)

        log_path = write_json_log({
            "url": create_url,
            "headers": {"Authorization": "<redacted>", "Content-Type": headers.get("Content-Type")},
            "payload": payload,
        }, prefix="kling_request")

        self.logger.info("Submitting Kling.ai image generation task")
        StoryOSLogger.log_user_action("system", "kling_task_submit", {
            "prompt_length": len(prompt),
            "model_name": self.model_name,
            "aspect_ratio": ratio,
        })

        try:
            response: Response = self.session.post(create_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            task_response = cast(JsonDict, response.json())
            append_json_log(log_path, {
                "type": "create_task_response",
                "status_code": response.status_code,
                "body": task_response,
            })
        except Exception as exc:
            response_obj = cast(Optional[Response], getattr(exc, "response", None))
            status_code: Optional[int] = getattr(response_obj, "status_code", None) if response_obj is not None else None
            append_json_log(log_path, {
                "type": "create_task_error",
                "error": str(exc),
                "status_code": status_code,
            })
            raise

        task_data = self._extract_task_data(task_response)
        task_id: str = task_data["task_id"]

        self.logger.debug(f"Kling.ai task submitted (task_id={task_id})")

        task_created = db.create_visualization_task({
            "task_id": task_id,
            "session_id": session_id,
            "message_id": message_id,
            "prompt": prompt,
            "model_name": payload.get("model_name"),
            "aspect_ratio": payload.get("aspect_ratio"),
            "task_status": task_data.get("task_status"),
            "task_status_msg": task_data.get("task_status_msg"),
        })

        if not task_created:
            self.logger.warning("Visualization task %s could not be persisted", task_id)

        final_task_data = self._poll_task_until_ready(task_id, headers=headers)
        append_json_log(log_path, {
            "type": "task_poll_complete",
            "task_data": final_task_data,
        })
        image_url = self._extract_image_url(final_task_data)

        StoryOSLogger.log_user_action("system", "kling_task_completed", {
            "task_id": task_id,
            "image_url_present": bool(image_url),
        })

        image_bytes = self._download_image(image_url)
        append_json_log(log_path, {
            "type": "image_download",
            "image_url": image_url,
            "content_bytes": len(image_bytes),
        })

        db.update_visualization_task(task_id, {
            "task_status": final_task_data.get("task_status"),
            "task_status_msg": final_task_data.get("task_status_msg"),
            "image_url": image_url,
            "task_result": final_task_data.get("task_result"),
            "image_retrieved_at": datetime.utcnow().isoformat(),
        })

        return VisualizationResponse(
            task_id=task_id,
            image_url=image_url,
            task_status=final_task_data.get("task_status"),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_headers(self) -> Dict[str, str]:
        token = self._get_jwt_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _build_url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    def _extract_task_data(self, response_json: JsonDict) -> _KlingTaskData:
        code = response_json.get("code")
        if code not in (0, None):
            message = response_json.get("message", "Unknown Kling.ai error")
            raise RuntimeError(f"Kling.ai create task failed ({code}): {message}")

        data = response_json.get("data")
        if not isinstance(data, dict):
            raise ValueError("Kling.ai create task response missing data object")

        task_id = data.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("Kling.ai create task response missing task_id")

        return cast(_KlingTaskData, data)

    def _poll_task_until_ready(self, task_id: str, *, headers: Dict[str, str]) -> _KlingTaskData:
        query_url = self._build_url(self.QUERY_TASK_PATH_TEMPLATE.format(task_id=task_id))
        start_time = time.time()
        db = get_db_manager()

        while True:
            if time.time() - start_time > self.poll_timeout:
                db.update_visualization_task(task_id, {
                    "task_status": "timeout",
                    "task_status_msg": "Polling timed out",
                })
                raise TimeoutError("Timed out waiting for Kling.ai image generation to complete")

            response: Response = self.session.get(query_url, headers=headers, timeout=30)
            response.raise_for_status()
            payload = cast(JsonDict, response.json())

            code = payload.get("code")
            if code not in (0, None):
                message = payload.get("message", "Unknown Kling.ai error")
                db.update_visualization_task(task_id, {
                    "task_status": "error",
                    "task_status_msg": message,
                })
                raise RuntimeError(f"Kling.ai query task failed ({code}): {message}")

            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("Kling.ai query task response missing data object")

            data_dict = cast(_KlingTaskData, data)
            status = (data_dict.get("task_status") or "").lower()
            status_msg: Optional[str] = data_dict.get("task_status_msg")

            db.update_visualization_task(task_id, {
                "task_status": status,
                "task_status_msg": status_msg,
            })

            if status == "succeed":
                return data_dict

            if status == "failed":
                db.update_visualization_task(task_id, {
                    "task_status": status,
                    "task_status_msg": status_msg or "Task failed",
                })
                raise RuntimeError(f"Kling.ai task {task_id} failed: {status_msg}")

            time.sleep(self.poll_interval)

    def _extract_image_url(self, task_data: _KlingTaskData) -> str:
        result = task_data.get("task_result")
        if not isinstance(result, dict):
            raise ValueError("Kling.ai task result missing task_result data")

        images = result.get("images")
        if not isinstance(images, list) or not images:
            raise ValueError("Kling.ai task result does not contain any images")

        first_image = images[0]
        if not isinstance(first_image, dict):
            raise ValueError("Kling.ai task image entry is not a dictionary")

        image_url = first_image.get("url")
        if not isinstance(image_url, str) or not image_url:
            raise ValueError("Kling.ai task image entry missing URL")

        return image_url

    def _download_image(self, image_url: str) -> bytes:
        if not image_url:
            raise ValueError("Image URL is required to download Kling.ai image")

        self.logger.debug(f"Downloading Kling.ai image from {image_url}")

        response: Response = self.session.get(image_url, timeout=60)
        response.raise_for_status()
        return response.content

    # ------------------------------------------------------------------
    # JWT utilities
    # ------------------------------------------------------------------
    def _get_jwt_token(self) -> str:
        now = time.time()
        if self._cached_token and now < self._token_expiry - 30:
            return self._cached_token

        header: Dict[str, object] = {
            "alg": "HS256",
            "typ": "JWT",
        }
        issued_at = int(now)
        payload: Dict[str, object] = {
            "iss": self.access_key,
            "iat": issued_at,
            "exp": issued_at + self.jwt_ttl,
            "nbf": issued_at - 5,
        }

        token = self._encode_jwt(header, payload)
        self._cached_token = token
        self._token_expiry = issued_at + self.jwt_ttl
        return token

    def _encode_jwt(self, header: Mapping[str, object], payload: Mapping[str, object]) -> str:
        header_segment = self._base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_segment = self._base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = header_segment + b"." + payload_segment
        signature = hmac.new(self.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
        signature_segment = self._base64url_encode(signature)
        return b".".join([header_segment, payload_segment, signature_segment]).decode("utf-8")

    @staticmethod
    def _base64url_encode(data: bytes) -> bytes:
        return base64.urlsafe_b64encode(data).rstrip(b"=")


__all__ = ["KlingClient"]

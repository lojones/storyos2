"""Utility helpers for working with model inputs and outputs."""

from __future__ import annotations

import json
from typing import Any, Dict, Type, TypeVar

from backend.logging_config import get_logger


class ModelUtils:
    """Helpers for model related data processing."""

    _logger = get_logger("model_utils")

    T = TypeVar("T")

    @staticmethod
    def json_from_string(value: str) -> Dict[str, Any]:
        """Parse a JSON object from a string, raising ValueError on failure."""
        logger = ModelUtils._logger
        logger.debug("Parsing JSON string of length %s", len(value) if value else 0)

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON string: %s", exc)
            raise ValueError(f"Invalid JSON string: {exc}") from exc

        if not isinstance(parsed, dict):
            logger.error("Parsed JSON is not an object: type=%s", type(parsed).__name__)
            raise ValueError("Parsed JSON is not an object")

        logger.info("Successfully parsed JSON object with %s keys", len(parsed))
        return parsed

    @staticmethod
    def model_from_json(data: Dict[str, Any], model_cls: Type[T]) -> T:
        """Instantiate a Pydantic model from JSON data.

        Example:
            >>> from backend.models.image_prompts import VisualPrompts
            >>> payload = {
            ...     "visual_prompt_1": "First prompt",
            ...     "visual_prompt_2": "Second prompt",
            ...     "visual_prompt_3": "Third prompt",
            ... }
            >>> ModelUtils.model_from_json(payload, VisualPrompts)
            VisualPrompts(visual_prompt_1='First prompt', ...)
        """
        logger = ModelUtils._logger
        logger.debug("Creating %s from JSON with keys: %s", model_cls.__name__, list(data.keys()))

        factory = getattr(model_cls, "from_dict", None)

        try:
            if callable(factory):
                logger.debug("Using %s.from_dict for instantiation", model_cls.__name__)
                instance = factory(data)  # type: ignore[misc]
            else:
                instance = model_cls(**data)  # type: ignore[arg-type]
        except Exception as exc:
            logger.error("Failed to instantiate %s: %s", model_cls.__name__, exc)
            raise

        if not isinstance(instance, model_cls):
            logger.error("Instance is not of type %s: got %s", model_cls.__name__, type(instance).__name__)
            raise TypeError(f"Instance is not of type {model_cls.__name__}: got {type(instance).__name__}")

        logger.info("Successfully created %s instance", model_cls.__name__)
        return instance

    @staticmethod
    def model_from_string(json_str: str, model_cls: Type[T]) -> T:
        """Instantiate a Pydantic model from a JSON string.

        Example:
            >>> from backend.models.image_prompts import VisualPrompts
            >>> json_str = '''
            ... {
            ...     "visual_prompt_1": "First prompt",
            ...     "visual_prompt_2": "Second prompt",
            ...     "visual_prompt_3": "Third prompt"
            ... }
            ... '''
            >>> ModelUtils.model_from_json_str(json_str, VisualPrompts)
            VisualPrompts(visual_prompt_1='First prompt', ...)
        """
        json_data = ModelUtils.json_from_string(json_str)
        return ModelUtils.model_from_json(json_data, model_cls)
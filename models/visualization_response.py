"""Visualization response model."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class VisualizationResponse(BaseModel):
    """Represents the response payload from a Kling.ai image generation task."""

    task_id: str = Field(..., description="Identifier for the Kling.ai generation task")
    image_url: str = Field(..., description="Public URL for the generated image")
    content: bytes = Field(..., description="Raw image bytes returned from Kling.ai", repr=False)
    task_status: Optional[str] = Field(
        default=None,
        description="Final status returned by Kling.ai for the task"
    )

    model_config = {
        "arbitrary_types_allowed": True,
    }

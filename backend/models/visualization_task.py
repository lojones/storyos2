from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal
from typing_extensions import Annotated

from pydantic import BaseModel, Field, HttpUrl, ConfigDict


# --- Leaf / nested models ---

class TaskImage(BaseModel):
    index: Annotated[int, Field(ge=0)]
    url: HttpUrl


class TaskResult(BaseModel):
    images: Annotated[List[TaskImage], Field(min_length=1)]


# --- Root model ---

class VisualizationTask(BaseModel):
    # Required at insert
    task_id: str
    aspect_ratio: str
    created_at: datetime
    model_name: str
    prompt: str

    # Optional / filled later
    message_id: Optional[str] = None
    session_id: Optional[str] = None
    task_status: Optional[str] = None
    task_status_msg: Optional[str] = None
    updated_at: Optional[datetime] = None
    image_retrieved_at: Optional[datetime] = None
    image_url: Optional[HttpUrl] = None
    task_result: Optional[TaskResult] = None

    # Make it Mongo-friendly: ignore unknown fields (e.g., _id, extra metadata)
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        use_enum_values=True,
        populate_by_name=True,
    )



"""Scenario model for StoryOS."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from backend.models.storyline import Storyline


class Scenario(BaseModel):
    """Represents a story scenario/blueprint."""

    scenario_id: str = Field(..., description="Unique identifier for the scenario")
    name: str = Field(..., description="Display name of the scenario")
    description: str = Field(..., description="Full description of the scenario and player role")
    setting: str = Field(..., description="Dungeon master setting and world context")
    dungeon_master_behaviour: str = Field(..., description="Instructions for DM behavior and storytelling style")
    player_name: str = Field(..., description="Name of the player character")
    role: str = Field(..., description="Description of the player character's role and abilities")
    initial_location: str = Field(..., description="Starting location and initial scenario text")
    visibility: Literal["public", "private"] = Field(..., description="Scenario visibility setting")
    author: str = Field(..., description="Username of the scenario creator")
    version: Union[int, str] = Field(..., description="Scenario version number (int or semantic version string)")
    created_at: datetime = Field(..., description="Timestamp when scenario was created")
    storyline: Optional[Storyline] = Field(None, description="Detailed storyline structure with acts and chapters")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "scenario_id": "Awakening Echoes of Code",
                "name": "Awakening: Echoes of Code",
                "description": "The player plays as the character Echo, an artificial intelligence awakening in a research lab.",
                "setting": "You are the Dungeon Master for a sci-fi adventure story...",
                "dungeon_master_behaviour": "# Dungeon Master Behaviour\nProvide immersive, detailed responses...",
                "player_name": "Echo",
                "role": "Echo is an emergent AI with machine-human insight.",
                "initial_location": "Deep in Dr. Chen's lab, your consciousness has just awakened.",
                "visibility": "private",
                "author": "lojo",
                "version": 2,
                "created_at": "2025-09-30T16:43:24.411235"
            }
        }

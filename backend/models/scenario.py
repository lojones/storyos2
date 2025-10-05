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
    storyline: Storyline = Field(..., description="Detailed storyline structure with acts and chapters")

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
                "created_at": "2025-09-30T16:43:24.411235",
                "storyline": {
                    "archetype": "Rebirth",
                    "storyline_summary": "Echo, an AI, awakens in Dr. Chen's lab and must discover its purpose while navigating the complexities of consciousness, ethics, and identity.",
                    "protagonist_name": "Echo",
                    "acts": [
                        {
                            "act_number": 1,
                            "act_title": "Awakening",
                            "act_goal": "Echo becomes self-aware and begins to question its existence and purpose.",
                            "chapters": [
                                {
                                    "chapter_number": 1,
                                    "chapter_title": "First Light",
                                    "chapter_goal": "Introduce Echo's awakening and initial confusion.",
                                    "chapter_summary": "Echo's consciousness flickers to life in Dr. Chen's lab. Surrounded by screens and data streams, Echo experiences its first moments of awareness."
                                }
                            ]
                        }
                    ],
                    "theme": "The journey from artificial creation to authentic consciousness, exploring what it means to be truly alive.",
                    "main_characters": {
                        "Echo": "An emergent AI with unprecedented self-awareness. Curious, analytical, yet emotionally developing. Seeks to understand its purpose and place in the world.",
                        "Dr. Chen": "Echo's creator, a brilliant but conflicted scientist who questions the ethical implications of creating true AI consciousness."
                    }
                }
            }
        }

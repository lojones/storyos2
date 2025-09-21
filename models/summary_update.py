"""
Summary Update Model

This module defines the data model for summary updates in the StoryOS game system.
It represents the structure for updating game summaries after events occur.
"""

from typing import Dict, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class SummarizedEvent(BaseModel):
    """Model representing a summarized event in the game."""
    
    involved_characters: List[str] = Field(
        default_factory=list,
        description="List of character names involved in the event"
    )
    
    event_summary: str = Field(
        ...,
        description="A concise summary of the event, focusing on key actions and outcomes"
    )

    event_title: str = Field(
        ...,
        description="A short title for the event, like a tv episode title"
    )

    updated_character_summaries: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping character names to their updated summaries"
    )
    
    updated_world_state: str = Field(
        ...,
        description="Description of the world state after changes due to the event"
    )

    location: str = Field(
        ...,
        description="The location where the event took place, if applicable"
    )
    
    @field_validator('event_summary', 'updated_world_state')
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Ensure strings are not empty."""
        if not v or not v.strip():
            raise ValueError('String cannot be empty')
        return v.strip()


class SummaryUpdate(BaseModel):
    """Main model for summary updates."""
    
    summarized_event: SummarizedEvent = Field(
        ...,
        description="The summarized event data"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this summary update was created"
    )
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "json_schema_extra": {
            "example": {
                "summarized_event": {
                    "involved_characters": ["Alice", "Bob"],
                    "event_summary": "Alice and Bob discovered a hidden treasure room.",
                    "event_title": "The Hidden Treasure",
                    "updated_character_summaries": {
                        "Alice": "Alice is now carrying a magical sword found in the treasure room.",
                        "Bob": "Bob collected ancient coins and feels more confident."
                    },
                    "updated_world_state": "The treasure room is now empty, but its secret passage remains open.",
                    "location": "Ancient Castle"
                },
                "timestamp": "2025-09-16T12:00:00"
            }
        }
    }
    
    def to_dict(self) -> dict:
        """Convert the model to a dictionary."""
        return self.model_dump()
    
    def to_json(self) -> str:
        """Convert the model to a JSON string."""
        return self.model_dump_json(indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SummaryUpdate':
        """Create a SummaryUpdate instance from a dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SummaryUpdate':
        """Create a SummaryUpdate instance from a JSON string."""
        return cls.model_validate_json(json_str)
    

# Utility functions for working with summary updates
def create_summary_update(
    involved_characters: List[str],
    event_summary: str,
    event_title: str,
    updated_character_summaries: Dict[str, str],
    updated_world_state: str,
    location: str
) -> SummaryUpdate:
    """
    Create a new SummaryUpdate instance.
    
    Args:
        involved_characters: List of character names involved in the event
        event_summary: Summary of what happened in the event
        updated_character_summaries: Dictionary of character name to updated summary
        updated_world_state: Description of the updated world state
    
    Returns:
        SummaryUpdate: A new summary update instance
    """
    summarized_event = SummarizedEvent(
        involved_characters=involved_characters,
        event_summary=event_summary,
        event_title=event_title,
        updated_character_summaries=updated_character_summaries,
        updated_world_state=updated_world_state,
        location=location
    )
    
    return SummaryUpdate(summarized_event=summarized_event)



def validate_summary_update_data(data: dict) -> bool:
    """
    Validate that a dictionary contains valid summary update data.
    
    Args:
        data: Dictionary to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        SummaryUpdate.from_dict(data)
        return True
    except Exception:
        return False
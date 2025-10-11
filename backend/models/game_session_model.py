"""
Game Session Models for StoryOS v2
Pydantic models for game session data validation and serialization
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from bson import ObjectId
from backend.models.summary_update import SummaryUpdate
from backend.models.storyline import Storyline


class StoryEvent(BaseModel):
    """Model for individual story events in the timeline"""
    
    event_datetime: datetime = Field(..., description="When the event occurred")
    event_title: str = Field(..., description="Short title for the event")
    event_description: str = Field(..., description="Detailed description of the event")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "event_datetime": "2025-01-15T10:30:00Z",
                "event_title": "Entered the Tavern",
                "event_description": "The player entered the Rusty Dragon tavern and spoke with the innkeeper"
            }
        }


class CharacterStory(BaseModel):
    """Model for character summaries"""
    
    character_story: str = Field(..., description="Summary of the character's story and current state")
    
    class Config:
        json_schema_extra = {
            "example": {
                "character_story": "An experienced warrior who has been traveling for months seeking adventure"
            }
        }


class GameSession(BaseModel):
    """Model for game session data (StorySummary)"""
    
    # MongoDB ObjectId (optional for new sessions)
    id: Optional[str] = Field(default=None, alias="_id", description="MongoDB document ID")
    
    # Core session metadata
    created_at: datetime = Field(..., description="When the session was created")
    last_updated: datetime = Field(..., description="When the session was last updated")
    user_id: str = Field(..., description="ID of the user who owns this session")
    scenario_id: str = Field(..., description="ID of the scenario being played")
    # game_session_id: int = Field(..., description="Unique game session identifier")
    version: int = Field(default=1, description="Version number for optimistic locking")
    
    # Game state data
    timeline: List[StoryEvent] = Field(default_factory=list, description="Chronological list of story events")
    character_summaries: Dict[str, CharacterStory] = Field(
        default_factory=dict,
        description="Character summaries keyed by character name"
    )
    world_state: str = Field(..., description="Current state of the game world")
    last_scene: str = Field(..., description="Current scenario summary")
    current_location: Optional[str] = Field(default=None, description="Current location of the player")
    current_act: int = Field(default=1, description="Current act number in the storyline")
    current_chapter: int = Field(default=1, description="Current chapter number in the storyline")
    storyline: Storyline = Field(..., description="Storyline structure with acts and chapters")
    turn_count: int = Field(default=0, description="Number of story turns (player actions) completed")
    game_speed: int = Field(default=4, description="Story progression speed (1-10, higher = faster chapter advancement)")
    deleted: bool = Field(default=False, description="Whether the game session has been soft-deleted")
    
    @validator('created_at', 'last_updated', pre=True)
    def parse_datetime(cls, v):
        """Parse datetime from various formats"""
        if isinstance(v, str):
            try:
                # Try parsing ISO format
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                # Try parsing without timezone info
                return datetime.fromisoformat(v)
        elif isinstance(v, datetime):
            return v
        else:
            raise ValueError(f"Invalid datetime format: {v}")

    # @validator('game_session_id')
    # def validate_game_session_id(cls, v):
    #     """Ensure game_session_id is a positive integer"""
    #     if not isinstance(v, int) or v <= 0:
    #         raise ValueError("game_session_id must be a positive integer")
    #     return v

    @validator('timeline')
    def validate_timeline(cls, v):
        """Ensure timeline is sorted by datetime"""
        if v:
            sorted_timeline = sorted(v, key=lambda x: x.event_datetime)
            return sorted_timeline
        return v
    
    @validator('user_id', 'scenario_id', 'world_state', 'last_scene')
    def validate_non_empty_strings(cls, v):
        """Ensure required string fields are not empty"""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    class Config:
        # Allow field aliases (for MongoDB _id)
        validate_by_name = True
        # JSON encoding for datetime objects
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }
        # Example schema
        json_schema_extra = {
            "example": {
                "created_at": "2025-01-15T10:00:00Z",
                "last_updated": "2025-01-15T11:30:00Z",
                "user_id": "user123",
                "scenario_id": "fantasy_dungeon_v1",
                "game_session_id": 1705320000123,
                "version": 1,
                "timeline": [
                    {
                        "event_datetime": "2025-01-15T10:05:00Z",
                        "event_title": "Adventure Begins",
                        "event_description": "The hero starts their journey in the village square"
                    }
                ],
                "character_summaries": {
                    "Hero": {
                        "character_story": "A brave adventurer seeking glory and treasure"
                    },
                    "Village Elder": {
                        "character_story": "A wise old man who gives guidance to travelers"
                    }
                },
                "world_state": "The village is peaceful, but rumors of danger lurk in the nearby forest",
                "last_scene": "The hero has just arrived in the village and is gathering information",
                "current_location": "Village Square",
                "current_act": 1,
                "current_chapter": 1,
                "turn_count": 0,
                "game_speed": 4,
                "deleted": False
            }
        }
    
    def add_story_event(self, title: str, description: str, event_time: Optional[datetime] = None) -> None:
        """Add a new story event to the timeline"""
        if event_time is None:
            event_time = datetime.utcnow()
        
        event = StoryEvent(
            event_datetime=event_time,
            event_title=title,
            event_description=description
        )
        
        self.timeline.append(event)
        # Keep timeline sorted
        self.timeline.sort(key=lambda x: x.event_datetime)
        self.last_updated = datetime.utcnow()
    
    def update_character_summary(self, character_name: str, character_story: str) -> None:
        """Update or add a character summary"""
        self.character_summaries[character_name] = CharacterStory(character_story=character_story)
        self.last_updated = datetime.utcnow()
    
    def update_world_state(self, new_state: str) -> None:
        """Update the world state"""
        self.world_state = new_state
        self.last_updated = datetime.utcnow()
    
    def update_last_scene(self, new_scene: str) -> None:
        """Update the last scene"""
        self.last_scene = new_scene
        self.last_updated = datetime.utcnow()

    def update_current_location(self, new_location: str) -> None:
        """Update the current location"""
        self.current_location = new_location
        self.last_updated = datetime.utcnow()

    def update_current_act(self, act_number: int) -> None:
        """Update the current act"""
        self.current_act = act_number
        self.last_updated = datetime.utcnow()

    def update_current_chapter(self, chapter_number: int) -> None:
        """Update the current chapter"""
        self.current_chapter = chapter_number
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = self.dict(by_alias=True, exclude_unset=True)
        
        # Convert datetime objects to ISO strings
        if 'created_at' in data:
            data['created_at'] = self.created_at.isoformat()
        if 'last_updated' in data:
            data['last_updated'] = self.last_updated.isoformat()
        
        # Convert timeline events
        if 'timeline' in data:
            data['timeline'] = [
                {
                    'event_datetime': event.event_datetime.isoformat(),
                    'event_title': event.event_title,
                    'event_description': event.event_description
                }
                for event in self.timeline
            ]
        
        # Convert character summaries
        if 'character_summaries' in data:
            data['character_summaries'] = {
                name: {'character_story': char.character_story}
                for name, char in self.character_summaries.items()
            }

        # Convert storyline
        if 'storyline' in data:
            data['storyline'] = self.storyline.dict()

        return data
    
    def update_act_chapter(self, act_number: int, chapter_number: int) -> None:
        """Update the current act and chapter"""
        self.current_act = act_number
        self.current_chapter = chapter_number
        self.last_updated = datetime.utcnow()

    def increment_turn_count(self) -> None:
        """Increment the turn count by 1"""
        self.turn_count += 1
        self.last_updated = datetime.utcnow()

    def update(self, summary_update: SummaryUpdate) -> None:
        self.add_story_event(summary_update.summarized_event.event_title, summary_update.summarized_event.event_summary)
        for name, char_summary in summary_update.summarized_event.updated_character_summaries.items():
            self.update_character_summary(name, char_summary)
        self.update_world_state(summary_update.summarized_event.updated_world_state)
        self.update_last_scene(summary_update.summarized_event.event_summary)
        self.update_current_location(summary_update.summarized_event.location)
        self.update_act_chapter(summary_update.summarized_event.current_act, summary_update.summarized_event.current_chapter)


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameSession':
        """Create GameSession from dictionary (e.g., from database)"""
        # Handle MongoDB ObjectId
        if '_id' in data:
            data['_id'] = str(data['_id'])

        # Remove game_session_id if present (deprecated field)
        if 'game_session_id' in data:
            del data['game_session_id']

        # Parse timeline events
        if 'timeline' in data:
            timeline_data = []
            for event_data in data['timeline']:
                timeline_data.append(StoryEvent(**event_data))
            data['timeline'] = timeline_data

        # Parse character summaries
        if 'character_summaries' in data:
            char_summaries = {}
            for name, char_data in data['character_summaries'].items():
                char_summaries[name] = CharacterStory(**char_data)
            data['character_summaries'] = char_summaries

        # Parse storyline
        if 'storyline' in data:
            data['storyline'] = Storyline(**data['storyline'])

        return cls(**data)


# Utility functions for working with game sessions
class GameSessionUtils:
    """Utility functions for game session operations"""
    
    @staticmethod
    def create_new_session(user_id: str, scenario_id: str, game_session_id: int, storyline: Storyline) -> GameSession:
        """Create a new game session with default values"""
        now = datetime.utcnow()

        return GameSession(
            created_at=now,
            last_updated=now,
            user_id=user_id,
            scenario_id=scenario_id,
            # game_session_id=game_session_id,
            version=1,
            timeline=[],
            character_summaries={},
            world_state="Game session initialized",
            last_scene="Adventure is about to begin",
            current_location="Players bedroom",
            current_act=1,
            current_chapter=1,
            storyline=storyline,
            turn_count=0,
            game_speed=4,
            deleted=False
        )
    
    @staticmethod
    def validate_session_data(data: Dict[str, Any]) -> List[str]:
        """Validate session data and return list of errors"""
        errors = []
        
        try:
            GameSession.from_dict(data)
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    @staticmethod
    def merge_session_updates(existing: GameSession, updates: Dict[str, Any]) -> GameSession:
        """Merge updates into existing session"""
        # Convert existing session to dict
        session_data = existing.to_dict()
        
        # Apply updates
        for key, value in updates.items():
            if key in ['created_at', '_id']:
                # Don't allow updating these fields
                continue
            session_data[key] = value
        
        # Ensure last_updated is set
        session_data['last_updated'] = datetime.utcnow()
        
        return GameSession.from_dict(session_data)


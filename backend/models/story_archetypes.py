"""Story Archetypes models for StoryOS."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Chapter(BaseModel):
    """Represents a chapter within an act."""

    chapter_number: int = Field(..., description="Chapter number within the story")
    goal: str = Field(..., description="The goal or purpose of this chapter")


class Act(BaseModel):
    """Represents an act within a story archetype."""

    act_number: int = Field(..., description="Act number (1, 2, or 3)")
    name: str = Field(..., description="Name of the act")
    goal: str = Field(..., description="Overall goal of this act")
    chapters: List[Chapter] = Field(..., description="List of chapters in this act")


class Archetype(BaseModel):
    """Represents a story archetype with its structure."""

    name: str = Field(..., description="Name of the archetype")
    examples: List[str] = Field(..., description="List of example stories using this archetype")
    acts: List[Act] = Field(..., description="List of acts that make up this archetype")


class StoryStructure(BaseModel):
    """Defines the overall story structure."""

    acts_per_story: List[int] = Field(..., description="Number of chapters per act [Act1, Act2, Act3]")
    total_chapters: int = Field(..., description="Total number of chapters in the story")


class StoryArchetypes(BaseModel):
    """Root model containing all story archetypes and structure."""

    structure: StoryStructure = Field(..., description="Overall story structure definition")
    archetypes: List[Archetype] = Field(..., description="List of all available story archetypes")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "structure": {
                    "acts_per_story": [3, 5, 3],
                    "total_chapters": 11
                },
                "archetypes": [
                    {
                        "name": "Hero's Journey",
                        "examples": [
                            "Star Wars: A New Hope",
                            "The Matrix",
                            "Moana"
                        ],
                        "acts": [
                            {
                                "act_number": 1,
                                "name": "Setup",
                                "goal": "Show the hero's ordinary world, trigger the call to adventure, and force a commitment to change.",
                                "chapters": [
                                    {
                                        "chapter_number": 1,
                                        "goal": "Establish protagonist, their want/need, flaw, and everyday life."
                                    },
                                    {
                                        "chapter_number": 2,
                                        "goal": "Inciting incident disrupts normal; stakes and opposition are revealed."
                                    },
                                    {
                                        "chapter_number": 3,
                                        "goal": "Hero commits; crosses the threshold into a new world or path."
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }

    @classmethod
    def from_json_file(cls, file_path: str) -> StoryArchetypes:
        """Load story archetypes from a JSON file."""
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)

    def get_archetype(self, name: str) -> Archetype | None:
        """Get a specific archetype by name."""
        for archetype in self.archetypes:
            if archetype.name.lower() == name.lower():
                return archetype
        return None

    def get_archetype_names(self) -> List[str]:
        """Get list of all archetype names."""
        return [archetype.name for archetype in self.archetypes]

    def get_chapter_goal(self, archetype_name: str, chapter_number: int) -> str | None:
        """Get the goal for a specific chapter in an archetype."""
        archetype = self.get_archetype(archetype_name)
        if not archetype:
            return None

        for act in archetype.acts:
            for chapter in act.chapters:
                if chapter.chapter_number == chapter_number:
                    return chapter.goal

        return None

    def get_act_for_chapter(self, chapter_number: int) -> int:
        """Determine which act a chapter belongs to based on structure."""
        if chapter_number <= self.structure.acts_per_story[0]:
            return 1
        elif chapter_number <= self.structure.acts_per_story[0] + self.structure.acts_per_story[1]:
            return 2
        else:
            return 3

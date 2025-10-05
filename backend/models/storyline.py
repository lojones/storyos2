"""Storyline model for StoryOS."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class StorylineChapter(BaseModel):
    """Represents a chapter within an act of a storyline."""

    chapter_number: int = Field(..., description="Chapter number within the act")
    chapter_title: str = Field(..., description="Title of the chapter")
    chapter_goal: str = Field(..., description="The goal or purpose of this chapter")
    chapter_summary: str = Field(..., description="Detailed summary of what happens in this chapter")


class StorylineAct(BaseModel):
    """Represents an act within a storyline."""

    act_number: int = Field(..., description="Act number (1, 2, or 3)")
    act_title: str = Field(..., description="Title of the act")
    act_goal: str = Field(..., description="Overall goal of this act")
    chapters: List[StorylineChapter] = Field(..., description="List of chapters in this act")


class Storyline(BaseModel):
    """Represents a complete storyline for a scenario."""

    archetype: str = Field(..., description="The story archetype being used (e.g., 'Hero's Journey')")
    storyline_summary: str = Field(..., description="High-level summary of the entire story")
    protagonist_name: str = Field(..., description="Name of the main protagonist of the story")
    acts: List[StorylineAct] = Field(..., description="List of acts that make up this storyline")
    theme: Optional[str] = Field(None, description="The central theme or message of the story")
    main_characters: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping character names to their descriptions"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "archetype": "Hero's Journey",
                "storyline_summary": "Luke Skywalker, a restless farm boy on the desert planet Tatooine, is drawn into an intergalactic rebellion after discovering a hidden message from Princess Leia.",
                "protagonist_name": "Luke Skywalker",
                "acts": [
                    {
                        "act_number": 1,
                        "act_title": "The Call to Adventure",
                        "act_goal": "Introduce Luke's simple life on Tatooine, the discovery that shatters it, and his decision to leave home.",
                        "chapters": [
                            {
                                "chapter_number": 1,
                                "chapter_title": "A Farm Boy on Tatooine",
                                "chapter_goal": "Show Luke's mundane existence and his yearning for something beyond his life on the moisture farm.",
                                "chapter_summary": "Luke Skywalker lives under the guardianship of his aunt and uncle, repairing droids and staring longingly at the twin sunsets."
                            }
                        ]
                    }
                ],
                "theme": "Courage, self-belief, and faith in something greater can turn even an ordinary farm boy into a symbol of hope.",
                "main_characters": {
                    "Luke Skywalker": "A young, restless farm boy from Tatooine who dreams of adventure beyond his mundane life. Skilled pilot with latent Force abilities.",
                    "Princess Leia": "A courageous leader of the Rebellion, captured by the Empire while on a secret mission. Strong-willed and resourceful.",
                    "Han Solo": "A cynical smuggler and pilot of the Millennium Falcon. Self-interested but ultimately heroic.",
                    "Obi-Wan Kenobi": "An aging Jedi Master in hiding, mentor to Luke. Wise and connected to the Force."
                }
            }
        }

    def get_chapter_by_number(self, chapter_number: int) -> Optional[StorylineChapter]:
        """Get a specific chapter by its number across all acts."""
        for act in self.acts:
            for chapter in act.chapters:
                if chapter.chapter_number == chapter_number:
                    return chapter
        return None

    def get_act_by_number(self, act_number: int) -> Optional[StorylineAct]:
        """Get a specific act by its number."""
        for act in self.acts:
            if act.act_number == act_number:
                return act
        return None

    def get_total_chapters(self) -> int:
        """Get the total number of chapters across all acts."""
        return sum(len(act.chapters) for act in self.acts)

    def get_chapter_titles(self) -> List[str]:
        """Get a list of all chapter titles in order."""
        titles = []
        for act in self.acts:
            for chapter in act.chapters:
                titles.append(chapter.chapter_title)
        return titles

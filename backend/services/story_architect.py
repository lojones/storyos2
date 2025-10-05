"""Story Architect service for StoryOS.

Provides story structure and archetype management functionality.
"""

from __future__ import annotations

import json
import os
from typing import Optional, cast

from backend.logging_config import get_logger
from backend.models.story_archetypes import StoryArchetypes, Archetype
from backend.models.storyline import Storyline
from backend.utils.prompts import PromptCreator
from backend.utils.llm_utils import get_llm_utility


class StoryArchitectService:
    """Service for managing story archetypes and structure."""

    def __init__(self):
        """Initialize the story architect service."""
        self.logger = get_logger("story_architect")
        self._archetypes: Optional[StoryArchetypes] = None
        self._archetypes_file_path = "backend/config/story_architect/story_archetypes.json"

    def get_story_archetypes(self) -> StoryArchetypes:
        """
        Load and return story archetypes from configuration.

        Returns:
            StoryArchetypes: The loaded story archetypes model

        Raises:
            FileNotFoundError: If the archetypes JSON file is not found
            ValueError: If the JSON file is invalid or cannot be parsed
        """
        # Return cached version if already loaded
        if self._archetypes is not None:
            self.logger.debug("Returning cached story archetypes")
            return self._archetypes

        self.logger.info(f"Loading story archetypes from {self._archetypes_file_path}")

        try:
            # Check if file exists
            if not os.path.exists(self._archetypes_file_path):
                self.logger.error(f"Story archetypes file not found: {self._archetypes_file_path}")
                raise FileNotFoundError(f"Story archetypes file not found: {self._archetypes_file_path}")

            # Load from JSON file
            self._archetypes = StoryArchetypes.from_json_file(self._archetypes_file_path)

            # Log successful load with details
            archetype_names = self._archetypes.get_archetype_names()
            self.logger.info(
                f"Successfully loaded {len(archetype_names)} story archetypes: {', '.join(archetype_names)}"
            )
            self.logger.debug(f"Total chapters per story: {self._archetypes.structure.total_chapters}")

            return self._archetypes

        except FileNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error loading story archetypes: {str(e)}")
            raise ValueError(f"Failed to load story archetypes: {str(e)}")

    def reload_archetypes(self) -> StoryArchetypes:
        """
        Force reload of story archetypes from disk.

        Returns:
            StoryArchetypes: The freshly loaded story archetypes model
        """
        self.logger.info("Force reloading story archetypes from disk")
        self._archetypes = None
        return self.get_story_archetypes()

    def get_archetype_by_name(self, name: str) -> Optional["Archetype"]:
        """
        Get a specific archetype by name.

        Args:
            name: Name of the archetype to retrieve

        Returns:
            Optional archetype if found, None otherwise
        """
        archetypes = self.get_story_archetypes()
        return archetypes.get_archetype(name)

    def get_available_archetypes(self) -> list[str]:
        """
        Get list of available archetype names.

        Returns:
            List of archetype names
        """
        archetypes = self.get_story_archetypes()
        return archetypes.get_archetype_names()

    def generate_storyline(self, archetype: Archetype, description: str) -> Storyline:
        """
        Generate a complete storyline using LLM based on archetype and description.

        Args:
            archetype: The story archetype to follow
            description: User's scenario and storyline description

        Returns:
            Generated Storyline object

        Raises:
            ValueError: If LLM generation fails or returns invalid JSON
        """
        self.logger.info(f"Generating storyline using archetype: {archetype.name}")

        try:
            # Build prompt using PromptCreator
            prompt_creator = PromptCreator()
            messages = prompt_creator.build_storyline_creation_prompt(archetype, description)

            # Get LLM utility
            llm = get_llm_utility()

            # Call LLM with Storyline schema
            schema = Storyline.model_json_schema()
            response_json = llm.call_creative_llm_nostream(messages, schema, prompt_type="storyline-generation")

            # Parse and return Storyline object
            storyline_data = json.loads(response_json)
            storyline = Storyline.model_validate(storyline_data)

            self.logger.info(
                f"Successfully generated storyline with {len(storyline.acts)} acts and "
                f"{storyline.get_total_chapters()} chapters"
            )

            return storyline  # type: ignore[return-value]

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error generating storyline: {str(e)}")
            raise ValueError(f"Failed to generate storyline: {str(e)}")


# Global service instance
_story_architect_service: Optional[StoryArchitectService] = None


def get_story_architect_service() -> StoryArchitectService:
    """
    Get the global story architect service instance.

    Returns:
        StoryArchitectService: The singleton service instance
    """
    global _story_architect_service
    if _story_architect_service is None:
        _story_architect_service = StoryArchitectService()
    return _story_architect_service

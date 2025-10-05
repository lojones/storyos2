"""Story Architect API routes."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.models.story_archetypes import StoryArchetypes, Archetype
from backend.models.storyline import Storyline
from backend.services.story_architect import get_story_architect_service

router = APIRouter()


class GenerateStorylineRequest(BaseModel):
    """Request model for generating a storyline."""

    archetype_name: str
    description: str


@router.get("/archetypes")
async def get_story_archetypes() -> StoryArchetypes:
    """
    Get all story archetypes and structure information.

    Returns:
        StoryArchetypes: Complete story archetypes configuration including
                        structure and all available archetypes
    """
    try:
        service = get_story_architect_service()
        archetypes = service.get_story_archetypes()
        return archetypes
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load archetypes: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get("/archetypes/names")
async def get_archetype_names() -> List[str]:
    """
    Get list of available archetype names.

    Returns:
        List[str]: List of archetype names
    """
    try:
        service = get_story_architect_service()
        names = service.get_available_archetypes()
        return names
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get archetype names: {str(e)}",
        )


@router.get("/archetypes/{archetype_name}")
async def get_archetype_by_name(archetype_name: str) -> Archetype:
    """
    Get a specific archetype by name.

    Args:
        archetype_name: Name of the archetype (case-insensitive)

    Returns:
        Archetype: The requested archetype with all its acts and chapters
    """
    try:
        service = get_story_architect_service()
        archetype = service.get_archetype_by_name(archetype_name)

        if not archetype:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archetype '{archetype_name}' not found",
            )

        return archetype
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get archetype: {str(e)}",
        )


@router.post("/generate-storyline")
async def generate_storyline(request: GenerateStorylineRequest) -> Storyline:
    """
    Generate a complete storyline using LLM based on archetype and description.

    Args:
        request: Contains archetype_name and description

    Returns:
        Storyline: Complete generated storyline with acts and chapters
    """
    try:
        service = get_story_architect_service()

        # Get the archetype
        archetype = service.get_archetype_by_name(request.archetype_name)
        if not archetype:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archetype '{request.archetype_name}' not found",
            )

        # Generate storyline
        storyline = service.generate_storyline(archetype, request.description)

        return storyline

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate storyline: {str(e)}",
        )


__all__ = ["router"]

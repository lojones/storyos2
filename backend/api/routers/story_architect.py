"""Story Architect API routes."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.logging_config import get_logger
from backend.models.story_archetypes import StoryArchetypes, Archetype
from backend.models.storyline import Storyline
from backend.services.story_architect import get_story_architect_service

logger = get_logger(__name__)
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
    logger.info(f"GET /api/story-architect/archetypes - Get all archetypes request")
    try:
        service = get_story_architect_service()
        archetypes = service.get_story_archetypes()
        logger.info(f"GET /api/story-architect/archetypes - Returning {len(archetypes.archetypes)} archetypes")
        return archetypes
    except FileNotFoundError as e:
        logger.error(f"GET /api/story-architect/archetypes - File not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        logger.error(f"GET /api/story-architect/archetypes - Value error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load archetypes: {str(e)}",
        )
    except Exception as e:
        logger.error(f"GET /api/story-architect/archetypes - Unexpected error: {str(e)}")
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
    logger.info(f"GET /api/story-architect/archetypes/names - Get archetype names request")
    try:
        service = get_story_architect_service()
        names = service.get_available_archetypes()
        logger.info(f"GET /api/story-architect/archetypes/names - Returning {len(names)} archetype names")
        return names
    except Exception as e:
        logger.error(f"GET /api/story-architect/archetypes/names - Error: {str(e)}")
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
    logger.info(f"GET /api/story-architect/archetypes/{archetype_name} - Get archetype request")
    try:
        service = get_story_architect_service()
        archetype = service.get_archetype_by_name(archetype_name)

        if not archetype:
            logger.warning(f"GET /api/story-architect/archetypes/{archetype_name} - Archetype not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archetype '{archetype_name}' not found",
            )

        logger.info(f"GET /api/story-architect/archetypes/{archetype_name} - Returning archetype")
        return archetype
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET /api/story-architect/archetypes/{archetype_name} - Error: {str(e)}")
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
    logger.info(f"POST /api/story-architect/generate-storyline - Generate storyline request for archetype={request.archetype_name}, description_length={len(request.description)}")
    try:
        service = get_story_architect_service()

        # Get the archetype
        archetype = service.get_archetype_by_name(request.archetype_name)
        if not archetype:
            logger.warning(f"POST /api/story-architect/generate-storyline - Archetype '{request.archetype_name}' not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archetype '{request.archetype_name}' not found",
            )

        # Generate storyline
        storyline = service.generate_storyline(archetype, request.description)

        logger.info(f"POST /api/story-architect/generate-storyline - Successfully generated storyline for archetype={request.archetype_name}")
        return storyline

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"POST /api/story-architect/generate-storyline - Value error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"POST /api/story-architect/generate-storyline - Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate storyline: {str(e)}",
        )


__all__ = ["router"]

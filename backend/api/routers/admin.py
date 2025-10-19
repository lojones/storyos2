"""Administrative API routes."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.dependencies import get_db_manager_dep, require_admin
from backend.logging_config import get_logger
from backend.utils.db_utils import DatabaseManager

logger = get_logger(__name__)
router = APIRouter()


class UserRoleUpdate(BaseModel):
    role: str


class SystemPromptUpdate(BaseModel):
    content: str
    active: bool = True
    version: int | None = None
    prompt_type: str | None = None


@router.get("/stats")
async def get_stats(
    admin: dict = Depends(require_admin),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Dict[str, Any]:
    logger.info(f"GET /api/admin/stats - Stats request by admin user_id={admin['user_id']}")
    user_count = db_manager.get_user_count()
    scenario_count = len(db_manager.get_all_scenarios())
    session_count = 0
    if db_manager.db is not None:
        session_count = db_manager.db.active_game_sessions.count_documents({})
    logger.info(f"GET /api/admin/stats - Returning stats (users={user_count}, scenarios={scenario_count}, sessions={session_count})")
    return {
        "users": user_count,
        "scenarios": scenario_count,
        "active_sessions": session_count,
    }


@router.get("/users/pending")
async def get_pending_users(
    admin: dict = Depends(require_admin),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> List[Dict[str, Any]]:
    """Get all users with pending role"""
    logger.info(f"GET /api/admin/users/pending - Get pending users request by admin user_id={admin['user_id']}")
    users = db_manager.get_users_by_role("pending")
    # Remove password hash from response
    for user in users:
        if "_id" in user:
            user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
    logger.info(f"GET /api/admin/users/pending - Returning {len(users)} pending users")
    return users


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    admin: dict = Depends(require_admin),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Dict[str, Any]:
    """Update a user's role"""
    logger.info(f"PUT /api/admin/users/{user_id}/role - Update user role request by admin user_id={admin['user_id']}, new_role={payload.role}")
    # Validate role
    if payload.role not in ["admin", "user", "pending"]:
        logger.warning(f"PUT /api/admin/users/{user_id}/role - Invalid role={payload.role}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'admin', 'user', or 'pending'",
        )

    # Check if user exists
    user = db_manager.get_user(user_id)
    if not user:
        logger.warning(f"PUT /api/admin/users/{user_id}/role - User not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update role
    success = db_manager.update_user(user_id, {"role": payload.role})
    if not success:
        logger.error(f"PUT /api/admin/users/{user_id}/role - Failed to update user role")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role",
        )

    # Return updated user
    updated_user = db_manager.get_user(user_id)
    if updated_user:
        if "_id" in updated_user:
            updated_user["_id"] = str(updated_user["_id"])
        updated_user.pop("password_hash", None)
        logger.info(f"PUT /api/admin/users/{user_id}/role - Successfully updated user role to {payload.role}")
        return updated_user

    logger.info(f"PUT /api/admin/users/{user_id}/role - Updated user role to {payload.role}")
    return {"user_id": user_id, "role": payload.role}


@router.get("/system-prompts")
async def get_system_prompts(
    admin: dict = Depends(require_admin),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Dict[str, Any]:
    """Get both system prompts"""
    logger.info(f"GET /api/admin/system-prompts - Get system prompts request by admin user_id={admin['user_id']}")
    try:
        story_prompt = db_manager.get_active_system_prompt()
        if story_prompt and "_id" in story_prompt:
            story_prompt["_id"] = str(story_prompt["_id"])
    except Exception:
        story_prompt = None

    try:
        viz_prompt_doc = db_manager.system_prompt_actions.db.system_prompts.find_one({
            'active': True,
            'name': 'Default StoryOS Visualization System Prompt'
        })
        if viz_prompt_doc and "_id" in viz_prompt_doc:
            viz_prompt_doc["_id"] = str(viz_prompt_doc["_id"])
    except Exception:
        viz_prompt_doc = None

    logger.info(f"GET /api/admin/system-prompts - Returning system prompts (story={bool(story_prompt)}, viz={bool(viz_prompt_doc)})")
    return {
        "story_prompt": story_prompt,
        "visualization_prompt": viz_prompt_doc
    }


@router.put("/system-prompts/story")
async def update_story_prompt(
    payload: SystemPromptUpdate,
    admin: dict = Depends(require_admin),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Dict[str, Any]:
    """Update story system prompt"""
    logger.info(f"PUT /api/admin/system-prompts/story - Update story prompt request by admin user_id={admin['user_id']}")
    try:
        # Get current prompt to get its ID
        prompt = db_manager.get_active_system_prompt()
        if not prompt:
            logger.warning(f"PUT /api/admin/system-prompts/story - Story system prompt not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story system prompt not found",
            )

        # Update the prompt
        success = db_manager.update_system_prompt(prompt["_id"], payload.content)
        if not success:
            logger.error(f"PUT /api/admin/system-prompts/story - Failed to update story system prompt")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update story system prompt",
            )

        # Return updated prompt
        updated_prompt = db_manager.get_active_system_prompt()
        if updated_prompt and "_id" in updated_prompt:
            updated_prompt["_id"] = str(updated_prompt["_id"])
        logger.info(f"PUT /api/admin/system-prompts/story - Successfully updated story system prompt")
        return updated_prompt

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PUT /api/admin/system-prompts/story - Error updating story system prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating story system prompt: {str(e)}",
        )


@router.put("/system-prompts/visualization")
async def update_visualization_prompt(
    payload: SystemPromptUpdate,
    admin: dict = Depends(require_admin),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Dict[str, Any]:
    """Update visualization system prompt"""
    logger.info(f"PUT /api/admin/system-prompts/visualization - Update visualization prompt request by admin user_id={admin['user_id']}")
    try:
        success = db_manager.update_visualization_system_prompt(payload.content)
        if not success:
            logger.error(f"PUT /api/admin/system-prompts/visualization - Failed to update visualization system prompt")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update visualization system prompt",
            )

        # Return updated prompt
        viz_prompt_doc = db_manager.system_prompt_actions.db.system_prompts.find_one({
            'active': True,
            'name': 'Default StoryOS Visualization System Prompt'
        })
        if viz_prompt_doc and "_id" in viz_prompt_doc:
            viz_prompt_doc["_id"] = str(viz_prompt_doc["_id"])
        logger.info(f"PUT /api/admin/system-prompts/visualization - Successfully updated visualization system prompt")
        return viz_prompt_doc

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PUT /api/admin/system-prompts/visualization - Error updating visualization system prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating visualization system prompt: {str(e)}",
        )


__all__ = ["router"]

"""Game session API routes."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Iterable, List

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import (
    get_current_user,
    get_db_manager_dep,
    get_game_service,
)
from backend.api.schemas import (
    GameSessionCreate,
    GameSessionEnvelope,
    GameSpeedUpdate,
    SessionListResponse,
    VisualizationRequest,
    VisualizationResult,
)
from backend.logging_config import get_logger
from backend.models.message import Message
from backend.services.game_service import GameService
from backend.utils.db_utils import DatabaseManager
from backend.utils.visualization_utils import VisualizationManager

logger = get_logger(__name__)
router = APIRouter()


def _normalise_sessions(raw_sessions: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sessions: List[Dict[str, Any]] = []
    for session in raw_sessions:
        normalised = dict(session)
        session_id = normalised.pop("_id", None)
        if session_id is not None:
            normalised["_id"] = str(session_id)
        sessions.append(normalised)
    return sessions


@router.post("/sessions")
async def create_game_session(
    data: GameSessionCreate,
    current_user: dict = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service),
) -> Dict[str, str]:
    logger.info(f"POST /api/game/sessions - Create session request by user_id={current_user['user_id']}, scenario_id={data.scenario_id}")
    session_id = await game_service.create_game_session(current_user["user_id"], data.scenario_id)
    if not session_id:
        logger.error(f"POST /api/game/sessions - Failed to create session for user_id={current_user['user_id']}, scenario_id={data.scenario_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create game session",
        )
    logger.info(f"POST /api/game/sessions - Created session_id={session_id} for user_id={current_user['user_id']}")
    return {"session_id": session_id}


@router.get("/sessions", response_model=SessionListResponse)
async def list_user_sessions(
    current_user: dict = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service),
) -> SessionListResponse:
    logger.info(f"GET /api/game/sessions - List sessions request for user_id={current_user['user_id']}")
    sessions = await game_service.list_user_sessions(current_user["user_id"])
    logger.info(f"GET /api/game/sessions - Returning {len(sessions)} sessions for user_id={current_user['user_id']}")
    return SessionListResponse(sessions=_normalise_sessions(sessions))


@router.get("/sessions/{session_id}", response_model=GameSessionEnvelope)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service),
) -> GameSessionEnvelope:
    logger.info(f"GET /api/game/sessions/{session_id} - Load session request by user_id={current_user['user_id']}")
    data = await game_service.load_session(session_id)
    session = data["session"]
    if session.user_id != current_user["user_id"]:
        logger.warning(f"GET /api/game/sessions/{session_id} - Access denied for user_id={current_user['user_id']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    raw_messages = data.get("messages", [])
    messages: List[Message] = []
    for message in raw_messages:
        if isinstance(message, Message):
            messages.append(message)
        elif isinstance(message, dict):
            messages.append(Message.from_dict(message))
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Encountered unsupported message payload",
            )

    logger.info(f"GET /api/game/sessions/{session_id} - Returning session with {len(messages)} messages for user_id={current_user['user_id']}")
    return GameSessionEnvelope(session=session, messages=messages)


@router.post(
    "/sessions/{session_id}/messages/{message_id}/visualize",
    response_model=VisualizationResult,
)
async def visualize_prompt(
    session_id: str,
    message_id: str,
    payload: VisualizationRequest,
    current_user: dict = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> VisualizationResult:
    logger.info(f"POST /api/game/sessions/{session_id}/messages/{message_id}/visualize - Visualization request by user_id={current_user['user_id']}, prompt={payload.prompt[:50]}...")
    data = await game_service.load_session(session_id)
    session = data["session"]
    if session.user_id != current_user["user_id"]:
        logger.warning(f"POST /api/game/sessions/{session_id}/messages/{message_id}/visualize - Access denied for user_id={current_user['user_id']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    raw_messages = data.get("messages", [])
    messages: List[Message] = []
    for message in raw_messages:
        if isinstance(message, Message):
            messages.append(message)
        elif isinstance(message, dict):
            messages.append(Message.from_dict(message))
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Encountered unsupported message payload",
            )

    target = next(
        (msg for msg in messages if (msg.message_id or "") == message_id),
        None,
    )
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    prompts = target.visual_prompts or {}
    if not prompts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No visualization prompts available for this message",
        )

    prompt_value = payload.prompt.strip()
    if prompt_value not in prompts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt not associated with this message",
        )

    message_identifier = target.message_id or message_id

    try:
        visualization = await asyncio.to_thread(
            VisualizationManager.submit_prompt,
            prompt_value,
            session_id,
            message_identifier,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - network/runtime errors
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Visualization request failed",
        ) from exc

    if visualization.image_url:
        db_manager.add_image_url_to_visual_prompt(
            session_id,
            message_identifier,
            prompt_value,
            visualization.image_url,
        )

    logger.info(f"POST /api/game/sessions/{session_id}/messages/{message_id}/visualize - Visualization task_id={visualization.task_id} submitted, status={visualization.task_status}")
    return VisualizationResult(
        task_id=visualization.task_id,
        prompt=prompt_value,
        image_url=visualization.image_url,
        status=visualization.task_status,
    )


@router.patch("/sessions/{session_id}/game-speed")
async def update_game_speed(
    session_id: str,
    speed_update: GameSpeedUpdate,
    current_user: dict = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Dict[str, Any]:
    logger.info(f"PATCH /api/game/sessions/{session_id}/game-speed - Update game speed request by user_id={current_user['user_id']}, new_speed={speed_update.game_speed}")
    data = await game_service.load_session(session_id)
    session = data["session"]

    if session.user_id != current_user["user_id"]:
        logger.warning(f"PATCH /api/game/sessions/{session_id}/game-speed - Access denied for user_id={current_user['user_id']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    success = db_manager.update_game_session_fields(session_id, {"game_speed": speed_update.game_speed})

    if not success:
        logger.error(f"PATCH /api/game/sessions/{session_id}/game-speed - Failed to update game speed for session_id={session_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update game speed",
        )

    logger.info(f"PATCH /api/game/sessions/{session_id}/game-speed - Successfully updated game speed to {speed_update.game_speed}")
    return {"session_id": session_id, "game_speed": speed_update.game_speed}


@router.delete("/sessions/{session_id}")
async def delete_game_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Dict[str, str]:
    """Soft delete a game session and all its related data (chats, visualizations)"""
    logger.info(f"DELETE /api/game/sessions/{session_id} - Delete session request by user_id={current_user['user_id']}")
    # Load session to verify ownership
    data = await game_service.load_session(session_id)
    session = data["session"]

    if session.user_id != current_user["user_id"]:
        logger.warning(f"DELETE /api/game/sessions/{session_id} - Access denied for user_id={current_user['user_id']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Soft delete the game session
    session_deleted = db_manager.update_game_session_fields(session_id, {"deleted": True})
    if not session_deleted:
        logger.error(f"DELETE /api/game/sessions/{session_id} - Failed to delete game session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete game session",
        )

    # Soft delete related chat document
    chat_deleted = db_manager.delete_chat(session_id)

    # Soft delete related visualization tasks
    viz_deleted = db_manager.delete_visualizations(session_id)

    logger.info(f"DELETE /api/game/sessions/{session_id} - Successfully deleted session and related data (chats={chat_deleted}, visualizations={viz_deleted})")
    return {
        "session_id": session_id,
        "status": "deleted",
        "chat_deleted": str(chat_deleted),
        "visualizations_deleted": str(viz_deleted),
    }


__all__ = ["router"]

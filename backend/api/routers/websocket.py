"""WebSocket handlers for realtime story streaming."""
from __future__ import annotations

import asyncio
import json
from typing import Dict, Set

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.websockets import WebSocket, WebSocketDisconnect

from backend.api.dependencies import get_auth_service, get_game_service
from backend.services.auth_service import AuthService
from backend.services.game_service import GameService

router = APIRouter()


class GameWebSocketManager:
    """Maintain active websocket connections per session."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.setdefault(session_id, set()).add(websocket)

    async def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self.active_connections.get(session_id)
            if connections and websocket in connections:
                connections.remove(websocket)
                if not connections:
                    self.active_connections.pop(session_id, None)

    async def send_json(self, session_id: str, payload: dict) -> None:
        connections = self.active_connections.get(session_id, set())
        to_remove: Set[WebSocket] = set()
        for connection in connections:
            try:
                await connection.send_json(payload)
            except Exception:
                to_remove.add(connection)
        if to_remove:
            async with self._lock:
                connections = self.active_connections.get(session_id, set())
                for conn in to_remove:
                    connections.discard(conn)
                if not connections and session_id in self.active_connections:
                    self.active_connections.pop(session_id, None)


manager = GameWebSocketManager()


async def _ensure_session_membership(
    game_service: GameService,
    session_id: str,
    user_id: str,
) -> None:
    session_payload = await game_service.load_session(session_id)
    session = session_payload["session"]
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session access denied",
        )


@router.websocket("/game/{session_id}")
async def game_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str,
    auth_service: AuthService = Depends(get_auth_service),
    game_service: GameService = Depends(get_game_service),
) -> None:
    user = auth_service.resolve_user_from_token(token)
    await _ensure_session_membership(game_service, session_id, user["user_id"])
    await manager.connect(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            event_type = message.get("type")

            if event_type == "player_input":
                content = message.get("content", "")
                if not content:
                    await manager.send_json(
                        session_id,
                        {"type": "error", "message": "Empty player input"},
                    )
                    continue

                asyncio.create_task(
                    _stream_player_input(session_id, content, game_service)
                )

            elif event_type == "initial_story":
                asyncio.create_task(
                    _stream_initial_story(session_id, game_service)
                )
            else:
                await manager.send_json(
                    session_id,
                    {"type": "error", "message": "Unknown websocket event"},
                )

    except WebSocketDisconnect:
        await manager.disconnect(session_id, websocket)


async def _stream_initial_story(session_id: str, game_service: GameService) -> None:
    async for chunk in game_service.stream_initial_story(session_id):
        await manager.send_json(
            session_id,
            {"type": "story_chunk", "content": chunk},
        )
    await manager.send_json(session_id, {"type": "story_complete"})


async def _stream_player_input(
    session_id: str,
    content: str,
    game_service: GameService,
) -> None:
    async for chunk in game_service.stream_player_input(session_id, content):
        await manager.send_json(
            session_id,
            {"type": "story_chunk", "content": chunk},
        )
    await manager.send_json(session_id, {"type": "story_complete"})


__all__ = ["router"]

"""Pydantic schemas for API requests and responses."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.models.game_session_model import GameSession
from backend.models.message import Message


class Token(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")
    user_role: str


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = Field(default="user")


class AuthResponse(BaseModel):
    user_id: str
    role: str


class GameSessionCreate(BaseModel):
    scenario_id: str


class PlayerInput(BaseModel):
    content: str


class GameSessionEnvelope(BaseModel):
    session: GameSession
    messages: List[Message]


class SessionListResponse(BaseModel):
    sessions: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    status: str


class ScenarioPayload(BaseModel):
    scenario_id: str
    name: str
    description: Optional[str] = None

    class Config:
        extra = "allow"


class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        extra = "allow"


class VisualizationRequest(BaseModel):
    prompt: str


class VisualizationResult(BaseModel):
    task_id: str
    prompt: str
    image_url: Optional[str] = None
    status: Optional[str] = None


class GameSpeedUpdate(BaseModel):
    game_speed: int = Field(..., ge=1, le=10, description="Game speed value between 1 and 10")

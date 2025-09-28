"""Shared FastAPI dependencies for StoryOS."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.config.settings import Settings, get_settings
from backend.services.auth_service import AuthService
from backend.services.game_service import GameService
from backend.utils.db_utils import DatabaseManager, get_db_manager


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db_manager_dep() -> DatabaseManager:
    """Return the singleton database manager."""
    return get_db_manager()


def get_settings_dep() -> Settings:
    return get_settings()


def get_auth_service(
    settings: Settings = Depends(get_settings_dep),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> AuthService:
    return AuthService(settings=settings, db_manager=db_manager)


def get_game_service(
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> GameService:
    return GameService(db_manager=db_manager)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    return auth_service.resolve_user_from_token(token)


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


__all__ = [
    "oauth2_scheme",
    "get_db_manager_dep",
    "get_settings_dep",
    "get_auth_service",
    "get_game_service",
    "get_current_user",
    "require_admin",
]

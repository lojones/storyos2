"""Authentication service bridging data access and JWT handling."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException, status

from backend.config.settings import Settings
from backend.logging_config import get_logger
from backend.utils.auth import hash_password, verify_password
from backend.utils.db_utils import DatabaseManager, get_db_manager


class AuthService:
    """Small facade for user authentication and token management."""

    def __init__(
        self,
        *,
        settings: Settings,
        db_manager: Optional[DatabaseManager] = None,
    ) -> None:
        self.settings = settings
        self.db_manager = db_manager or get_db_manager()
        self.logger = get_logger("auth_service")

    # ------------------------------------------------------------------
    # User authentication helpers
    # ------------------------------------------------------------------
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Validate username/password against stored credentials."""
        user = self.db_manager.get_user(username)
        if not user:
            self.logger.debug("User %s not found during authentication", username)
            return None

        password_hash = user.get("password_hash")
        if not password_hash or not verify_password(password, password_hash):
            self.logger.debug("Invalid credentials supplied for user %s", username)
            return None

        return user

    def register_user(self, username: str, password: str, role: str = "user") -> bool:
        """Register a new user with hashed password."""
        if self.db_manager.user_exists(username):
            self.logger.info("Attempt to register existing user %s", username)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )

        password_hash = hash_password(password)
        created = self.db_manager.create_user(username, password_hash, role)
        if not created:
            self.logger.error("Failed to create user %s", username)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )
        return True

    # ------------------------------------------------------------------
    # JWT helpers
    # ------------------------------------------------------------------
    def create_access_token(self, user_id: str, role: str) -> str:
        """Return a signed JWT token for the supplied user."""
        expire_minutes = self.settings.jwt_access_token_expire_minutes
        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        payload = {"sub": user_id, "role": role, "exp": expire}
        token = jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )
        self.logger.debug("Issued access token for user=%s role=%s", user_id, role)
        return token

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode a JWT token and return payload."""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError as exc:  # pragma: no cover - runtime path
            self.logger.info("Expired JWT presented: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except jwt.PyJWTError as exc:
            self.logger.info("Invalid JWT presented: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        return payload

    def resolve_user_from_token(self, token: str) -> Dict[str, Any]:
        """Decode a token and ensure the backing user still exists."""
        payload = self.decode_token(token)
        user_id = payload.get("sub")
        role = payload.get("role")
        if not user_id or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication payload",
            )

        user = self.db_manager.get_user(user_id)
        if not user:
            self.logger.info("Token references missing user %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists",
            )

        return {"user_id": user_id, "role": user.get("role", role)}


__all__ = ["AuthService"]

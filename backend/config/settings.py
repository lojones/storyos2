"""Application settings and helpers."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class Settings:
    """Configuration values loaded from environment variables."""

    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "StoryOS API"))
    api_version: str = field(default_factory=lambda: os.getenv("API_VERSION", "3.0.0"))
    jwt_secret_key: str = field(
        default_factory=lambda: os.getenv("JWT_SECRET_KEY", "change-me")
    )
    jwt_algorithm: str = field(
        default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256")
    )
    jwt_access_token_expire_minutes: int = field(
        default_factory=lambda: int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))
    )
    websocket_base_url: str = field(
        default_factory=lambda: os.getenv("WEBSOCKET_BASE_URL", "ws://localhost:8000")
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()


__all__ = ["Settings", "get_settings"]

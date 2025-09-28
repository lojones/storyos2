"""Router exports for easy inclusion."""
from backend.api.routers import admin, auth, game, scenarios, websocket

__all__ = ["admin", "auth", "game", "scenarios", "websocket"]

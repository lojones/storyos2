"""FastAPI entrypoint for StoryOS."""
from __future__ import annotations

from fastapi import FastAPI

from backend.api.middleware import configure_cors
from backend.api.routers import admin, auth, game, scenarios, websocket
from backend.api.schemas import HealthResponse
from backend.config.settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.api_version)

configure_cors(app, settings)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(game.router, prefix="/api/game", tags=["game"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["scenarios"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")


__all__ = ["app"]

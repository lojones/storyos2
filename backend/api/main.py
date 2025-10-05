"""FastAPI entrypoint for StoryOS."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Load environment variables from .env file
load_dotenv()

from backend.api.middleware import configure_cors
from backend.api.routers import admin, auth, game, scenarios, story_architect, websocket
from backend.api.schemas import HealthResponse
from backend.config.settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.api_version)

configure_cors(app, settings)

# Serve static frontend files (for production deployment only)
# In development, Vite dev server handles the frontend
# IMPORTANT: Mount static files BEFORE registering API routes
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    # Mount static assets
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

# API routers - these are registered AFTER static mounts but BEFORE catch-all
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(game.router, prefix="/api/game", tags=["game"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["scenarios"])
app.include_router(story_architect.router, prefix="/api/story-architect", tags=["story-architect"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")


# SPA fallback - registered LAST so API routes take precedence
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve the React SPA for all non-API routes."""
        # This should never be reached for /api or /ws routes
        # because they're handled by routers registered above

        # Check if the requested file exists
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # Otherwise return index.html (SPA fallback)
        return FileResponse(frontend_dist / "index.html")


__all__ = ["app"]

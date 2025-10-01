"""Custom middleware initialisation for the FastAPI app."""
from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import Settings


def configure_cors(app: FastAPI, settings: Settings) -> None:
    """Attach CORS middleware using settings-defined origins.

    CORS is only needed for local development when frontend and backend
    run on different ports. In production (Azure), the frontend is served
    as static files by the backend, so they share the same origin.
    """
    # Only enable CORS if ALLOWED_ORIGINS is explicitly set (local development)
    if os.getenv("ALLOWED_ORIGINS"):
        print(f"🔧 CORS Debug: CORS middleware enabled")
        print(f"🔧 CORS Debug: Allowed origins: {settings.allowed_origins}")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        print(f"🔧 CORS Debug: CORS middleware disabled (production mode)")


__all__ = ["configure_cors"]

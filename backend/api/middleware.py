"""Custom middleware initialisation for the FastAPI app."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import Settings


def configure_cors(app: FastAPI, settings: Settings) -> None:
    """Attach CORS middleware using settings-defined origins."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


__all__ = ["configure_cors"]

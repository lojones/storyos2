"""Custom middleware initialisation for the FastAPI app."""
from __future__ import annotations

from fastapi import FastAPI

from backend.config.settings import Settings


def configure_cors(app: FastAPI, settings: Settings) -> None:
    """CORS configuration placeholder.

    CORS is not needed in development (Vite proxy handles it) or production
    (frontend served as static files by backend - same origin).
    """
    pass


__all__ = ["configure_cors"]

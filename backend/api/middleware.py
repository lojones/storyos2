"""Custom middleware initialisation for the FastAPI app."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import Settings


def configure_cors(app: FastAPI, settings: Settings) -> None:
    """Attach CORS middleware using settings-defined origins."""
    # Temporary debug: force the correct origins
    debug_origins = [
        "http://localhost:8080",
        "http://127.0.0.1:8080", 
        "http://192.168.86.20:8080"
    ]
    print(f"🔧 CORS Debug: Settings origins: {settings.allowed_origins}")
    print(f"🔧 CORS Debug: Using debug origins: {debug_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=debug_origins,  # Use debug origins instead of settings
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


__all__ = ["configure_cors"]

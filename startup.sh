#!/bin/bash
# Azure App Service startup script

# Start uvicorn server
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

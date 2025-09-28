# StoryOS AI Coding Agent Instructions

## Project Overview

StoryOS is an interactive narrative platform with a **FastAPI backend** and a **React (Vite) frontend**. The backend manages game state, user sessions, and LLM integration, while the frontend provides a responsive control center for running and visualizing stories. The system is designed for extensibility, supporting both REST and WebSocket communication.

## Architecture & Key Components

- **Backend (backend)**
  - `api/`: FastAPI app and routers (entrypoint: `main:app`)
  - `core/`: Legacy gameplay logic (do not expand; new logic goes in `services/`)
  - `services/`: Async facades/adapters over core logic and external APIs
  - `models/`: Pydantic schemas shared across routers/services
  - `utils/`: Data and LLM helpers
  - tests: Pytest-based API and logic tests

- **Frontend (src)**
  - `components/`: React UI components (PascalCase)
  - `pages/`: Route-level pages (e.g., `Game.tsx`)
  - `hooks/`: Custom React hooks (useX pattern)
  - `store/`: State management (colocate slices)
  - Uses TypeScript, Vite, and functional components

- **Shared**
  - docker-compose.yml: Full stack dev environment (API, frontend, MongoDB, Redis)
  - requirements.txt: Backend dependencies
  - README.md/AGENTS.md: Up-to-date workflows and conventions

## Developer Workflows

- **Backend**
  - Create venv: `python -m venv .venv && .venv\Scripts\activate`
  - Install: `pip install -r requirements.txt`
  - Run API: `uvicorn backend.api.main:app --reload --port 8000`
  - Test: `pytest backend/tests`
  - Env vars: Set `MONGODB_URI`, `JWT_SECRET_KEY`, `XAI_API_KEY`, etc.

- **Frontend**
  - Setup: `cd frontend && npm install`
  - Dev server: `npm run dev` (http://localhost:5173)
  - Test: Add tests under `frontend/src/tests/` (Vitest/Playwright)

- **Full Stack**
  - `docker-compose up --build` (runs API, frontend, MongoDB, Redis)

## Project-Specific Conventions

- **Backend**
  - Use PEP 8, type hints, snake_case for functions/modules, PascalCase for classes
  - Services should be thin adapters; put helpers in `utils/`
  - Place new tests in `backend/tests/test_*.py` and mock LLM calls

- **Frontend**
  - Components: PascalCase, colocate styles if needed
  - Hooks: `useX` naming, colocate with related logic
  - State: Use `store/` for slices, prefer functional components and TS interfaces

- **Commits/PRs**
  - Use imperative, scoped commit messages (e.g., `feat(backend): add websocket retry logic`)
  - PRs must pass `pytest` and `npm run build`
  - Document validation steps and attach screenshots/JSON for UI/API changes

## Integration & Data Flow

- **API**: REST endpoints for CRUD, WebSocket for real-time story/visualization streaming
- **LLM**: Integrate via `services/` (Grok, Kling, etc.); keys in .env (not tracked)
- **MongoDB**: Used for user, session, scenario, and chat storage (see README.md for schema hints)
- **Frontend**: Uses `gameAPI` and `GameWebSocket` for session and chat management

## Security & Configuration

- Secrets in .env (not tracked); update README.md and docker-compose.yml for new config
- Hash passwords, validate all user input, and restrict admin features by role

## Examples

- **Backend test**: `pytest backend/tests/test_api.py`
- **Frontend dev**: `npm run dev` in frontend
- **WebSocket usage**: See Game.tsx for streaming logic

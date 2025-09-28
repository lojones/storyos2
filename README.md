# StoryOS v3

React + FastAPI architecture for StoryOS, evolved from the original Streamlit prototype. The backend exposes REST and WebSocket endpoints for game state management while the frontend delivers a responsive control centre for running interactive stories.

## Project Layout

```
storyos2/
├── backend/
│   ├── api/                # FastAPI app and routers
│   ├── config/             # Environment-driven settings
│   ├── core/               # Legacy gameplay logic
│   ├── models/             # Pydantic models reused by API
│   ├── services/           # Async facades over legacy code
│   ├── utils/              # Data/LLM helpers (port from Streamlit)
│   └── tests/              # API test suite (pytest)
├── frontend/
│   ├── src/                # React + TypeScript app (Vite)
│   ├── package.json
│   └── vite.config.ts
├── requirements.txt        # Backend dependencies
└── docker-compose.yml      # Optional full stack runtime
```

## Prerequisites

- Python 3.11+
- Node 18+
- MongoDB and Redis (matching existing StoryOS services)

## Backend Setup

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

Environment variables:

```
export MONGODB_URI="mongodb://localhost:27017/storyos"
export JWT_SECRET_KEY="change-this"
export XAI_API_KEY="..."                        # existing LLM integration
export KLING_ACCESS_KEY="..."                    # optional: Kling.ai image generation
export KLING_SECRET_KEY="..."
```

Run the API (hot reload):

```bash
uvicorn backend.api.main:app --reload --port 8000
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev    # served at http://localhost:5173
```

Set `VITE_API_URL` or `VITE_WS_URL` in an `.env` file if the backend runs on a different host/port.

## Key API Routes

- `POST /api/auth/login` – OAuth2 password flow, returns JWT
- `POST /api/auth/register` – bootstrap admin or admin-managed onboarding
- `GET /api/game/sessions` – list sessions for the current user
- `POST /api/game/sessions` – create a session from a scenario blueprint
- `GET /api/game/sessions/{id}` – load session data and chat history
- `POST /api/game/sessions/{id}/messages/{messageId}/visualize` – generate a Kling.ai image for a prompt
- `GET /api/scenarios` – enumerate playable scenarios
- `GET /api/admin/stats` – environment metrics (requires admin role)
- `WS /ws/game/{session_id}?token=JWT` – real-time story streaming

## Testing

```bash
pytest backend/tests
```

## Docker (optional)

The root `docker-compose.yml` starts MongoDB, Redis, the FastAPI backend, and the React frontend. Supply environment variables via `.env` before running `docker-compose up`.

## Migration Notes

- All Streamlit components were relocated into `backend/utils` with a compatibility shim; they no longer require the Streamlit runtime.
- Legacy game logic remains unchanged but is accessed through async services that convert blocking generators into FastAPI-friendly streams.
- React frontend mirrors the original StoryOS pages (login, main menu, game console, scenarios, admin tools) with Redux Toolkit handling authentication state.

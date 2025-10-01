# Repository Guidelines

## Project Structure & Module Organization
- `backend/` hosts FastAPI code: routers in `api/routers/`, gameplay logic in `core/`, async façades in `services/`, and shared schemas in `models/`.
- `frontend/src/` contains the React app; components live under `components/`, pages under `pages/`, hooks in `hooks/`, and state resides in `store/`.
- Shared docs sit in `docs/`, static artwork in `assets/`, and API-focused tests in `backend/tests/`. Reuse these folders when adding features to keep responsibilities separated.

## Build, Test, and Development Commands
- Backend setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Run the API with hot reload: `uvicorn backend.api.main:app --reload --port 8000`.
- Frontend dev server: `cd frontend && npm install && npm run dev` (serves `http://localhost:5173`).
- Backend tests: `pytest backend/tests`.
- Full stack preview: `docker-compose up --build` brings up API, frontend, MongoDB, and Redis.

## Coding Style & Naming Conventions
- Follow PEP 8, four-space indentation, and type hints in Python files; modules and functions use `snake_case` while classes stay `PascalCase`.
- Keep services as thin adapters that delegate to `backend/core`; place external integrations or helpers under `backend/utils` rather than inflating routers.
- In the frontend, name components with `PascalCase`, hooks with the `useX` pattern, and colocate store slices in `frontend/src/store/`. Prefer functional components and TypeScript interfaces for props.

## Testing Guidelines
- Place new backend tests in `backend/tests/test_*.py`; mock LLM calls so deterministic fixtures drive assertions.
- When adding frontend behavior, create Vitest or Playwright tests under `frontend/src/tests/` (add the folder if missing) and mirror file names after the component under test.
- Aim to cover authentication flows, scenario loading, and streaming updates before requesting review.

## Commit & Pull Request Guidelines
- Use concise, imperative commit messages such as `feat: add websocket retry logic`; include a scope (`backend`, `frontend`) when helpful.
- Squash unrelated changes; each PR should describe the intent, list validation steps (commands run, test output), and attach screenshots or JSON snippets for UI/API changes.
- Confirm `pytest` and the TypeScript build (`npm run build`) both succeed before submitting.

## Security & Configuration Tips
- Keep secrets (`MONGODB_URI`, `JWT_SECRET_KEY`, `XAI_API_KEY`, Kling keys) in an untracked `.env`; load them via `dotenv` locally and through Docker Compose in shared environments.
- Update `README.md` and `docker-compose.yml` whenever new configuration values are required so deployment remains reproducible.

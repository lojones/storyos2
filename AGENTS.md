# Repository Guidelines

## Project Structure & Module Organization
StoryOS v2 centers on `app.py`, which orchestrates routing, session state, and Grok calls. Feature flows live under `pages/`; core turn resolution sits in `game/game_logic.py` with schemas in `models/`. Shared services—auth, MongoDB adapters, LLM helpers, validation, and session utilities—reside in `utils/`. Narrative seeds are stored in `data/`, log rotation targets `logs/`, and deployment overrides belong in `config/`. Keep secrets in a local `.env`; never commit credentials. Tests live in `tests/` and mirror feature boundaries (`test_game_logic.py`, etc.).

## Build, Test, and Development Commands
Activate the venv with `source .venv/bin/activate` (or PowerShell equivalent). Install deps via `pip install -r requirements.txt`. Launch the app locally using `streamlit run app.py`; fall back to `python -m streamlit run app.py` when needed. Use `python -m utils.initialize_db` to exercise database/log seeding without the UI. Run `pytest -q` before reviews and after meaningful changes.

## Coding Style & Naming Conventions
Target Python 3.11 with 4-space indentation. Use `snake_case` for functions, variables, and modules; reserve `PascalCase` for Pydantic models. Type-hint public functions, keep helpers small, and pull loggers with `get_logger("<module>")` or `StoryOSLogger`. Streamlit session mutations should go through `utils/st_session_management.py` utilities for consistency.

## Testing Guidelines
Write focused `pytest` modules named `tests/test_<feature>.py`. Mock `pymongo` and Grok clients to avoid remote calls. Capture representative chat transcripts when validating narrative changes. Aim for meaningful coverage on new logic and document any manual Streamlit walkthroughs when UI interactions shift. Always run `pytest -q` before opening a PR.

## Commit & Pull Request Guidelines
Use concise, lower-case, imperative commit subjects (e.g., `add session helpers`). PRs should summarize behaviour changes, mention linked tickets, and highlight data migrations or env updates. Attach screenshots for UI updates, note test results (`pytest`, manual flows), and tag owners of touched modules (`utils`, `pages`, `models`, `game`).

## Security & Configuration Tips
Set `XAI_API_KEY` and `OPENAI_BASE_URL=https://api.x.ai/v1` in your `.env`. Default models are `grok-4-0709` and `grok-3-mini`; keep them configurable. Guard first-run flows to seed the admin user only when `users` is empty and hash passwords via `utils/auth.py`.

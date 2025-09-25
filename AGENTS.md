# Repository Guidelines

## Project Structure & Module Organization
StoryOS v2 is a Streamlit RPG orchestrated by `app.py`, which handles routing, session state, and Grok API calls. Feature pages live in `pages/` (new/load game, scenarios, admin system prompt). Core turn logic resides in `game/game_logic.py`, with supporting schemas and examples in `models/`. Shared services—auth, MongoDB adapters, LLM utilities, validation, and session helpers—are grouped under `utils/`. Narrative seeds live in `data/`, runtime logs rotate in `logs/`, and `config/` is reserved for deployment overrides. Keep `.env` local; never commit credentials.

## Build, Test, and Development Commands
Activate the virtual environment (`source .venv/bin/activate` or `& .venv/Scripts/Activate.ps1`) and install dependencies via `pip install -r requirements.txt`. Launch the app with `streamlit run app.py` (fallback: `python -m streamlit run app.py`). For scripted checks, run modules directly (e.g., `python -m utils.initialize_db`) to exercise database or logging flows without the UI. Always export the expected `.env` keys before starting Streamlit.

## External Services & Configuration
The app speaks to xAI’s Grok models through the OpenAI-compatible client; set `XAI_API_KEY` and `OPENAI_BASE_URL=https://api.x.ai/v1`. Default models are `grok-4-0709` for rich narration and `grok-3-mini` for lightweight tasks—keep both configurable in code. MongoDB collections (`users`, `scenarios`, `saved_games`, `chats`, `system_prompts`) back authentication and persistence. First-run flows should seed an admin user when `users` is empty, so guard those paths and hash passwords via `auth.py`. Document any new env vars in PRs.

## Coding Style & Naming Conventions
Use Python 3.11 conventions: 4-space indentation, `snake_case` for functions/variables/modules, `PascalCase` for Pydantic models. Type hint public functions and favour small, composable helpers. Pull loggers with `get_logger("<module>")` and prefer `StoryOSLogger` helpers for structured events. Streamlit session state mutations should go through utilities in `utils/st_session_management.py` to stay consistent.

## Testing Guidelines
Add focused `pytest` coverage under `tests/`, naming files `test_<feature>.py`. Mock `pymongo` and Grok clients to avoid live calls, and record representative chat transcripts for regression checks. Run `pytest -q` before requesting review, and note any manual Streamlit walkthroughs when UI paths change.

## Commit & Pull Request Guidelines
History favours concise, lower-case subjects ("ui updates", "more refactors"). Continue that tone but aim for imperative verbs describing the change. Reference tickets, highlight migrations or data seeding, and mention impacted env vars. Pull requests should summarise behaviour, attach screenshots for UI tweaks, include `pytest` (or rationale if skipped), and ping owners of the affected modules (`utils`, `pages`, `models`, `game`).

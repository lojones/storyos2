# StoryOS v2 - AI Coding Agent Instructions

## Project Overview
StoryOS v2 is a Streamlit-based chat application that provides a web interface for interacting with xAI's Grok API. This is a **single-file application** focused on conversational AI functionality.

## Architecture & Key Components

### Core Application
- **`app.py`** - Complete application logic in a single file
  - Streamlit chat interface with session state management
  - xAI Grok API integration using OpenAI-compatible client
  - Environment-based configuration via `.env`

### Directory Structure
- **Empty directories**: `config/`, `data/`, `models/`, `pages/`, `utils/` - prepared for future expansion
- **`.venv/`** - Python virtual environment (Windows-specific paths)
- **`.vscode/launch.json`** - Debug configurations for VS Code

## Development Workflow

### Environment Setup
```powershell
# Activate virtual environment (Windows PowerShell)
& .venv/Scripts/Activate.ps1

# Install dependencies
pip install streamlit openai python-dotenv
```

### Running the Application
- **VS Code Debug**: Use "Streamlit App" launch configuration 
- **Command line**: `streamlit run app.py`
- **Python path**: Uses `.venv/Scripts/python.exe`

### Key Dependencies
- `streamlit` - Web UI framework
- `openai` - Client library (used for xAI API compatibility)
- `python-dotenv` - Environment variable management

## Configuration Patterns

### Environment Variables (`.env`)
```env
XAI_API_KEY=your_api_key_here
MONGODB_URI=mongodb_connection_string
MONGODB_USERNAME=username
MONGODB_PASSWORD=password
MONGODB_DATABASE_NAME=storyos
```

**Note**: MongoDB configuration exists but is not currently used in `app.py`

### API Integration
- Uses OpenAI client library with custom base URL: `https://api.x.ai/v1`
- Model: `grok-4-0709` (large, complex creative tasks)
- Model: `grok-3-mini` (quick, for simple tasks)
- Chat completions format compatible with OpenAI API structure

## Code Patterns & Conventions

### Streamlit Session State
```python
# Chat history management
if "messages" not in st.session_state:
    st.session_state.messages = []
```

### Error Handling
- API key validation with user-friendly error messages
- Direct display of missing configuration via `st.error()`

### Chat Flow
1. Display chat history from session state
2. Capture user input via `st.chat_input()`
3. Add user message to session state
4. Call Grok API with full conversation history
5. Display and store assistant response

## Development Guidelines

### When Adding Features
- **Database integration**: MongoDB configuration is ready but unused - connect via `MONGODB_URI`
- **Multi-page apps**: Use Streamlit's `pages/` directory for additional pages
- **Data persistence**: Utilize `data/` directory for local storage
- **Utilities**: Place helper functions in `utils/` directory
- **Configuration**: Expand `config/` for app-specific settings

### Testing & Debugging
- Use VS Code's integrated terminal with activated virtual environment
- Debug configurations available for both direct Python and Streamlit execution
- Check `.env` file exists and contains required API keys

### Dependency Management
- Currently using manual pip installation
- Consider adding `requirements.txt` for dependency tracking
- Virtual environment is Windows-specific (`.venv/Scripts/`)

## Future Architecture Considerations
- MongoDB integration is configured but not implemented
- Directory structure suggests planned expansion beyond single-file app
- Consider modularizing `app.py` as features grow



---

# Copilot Instruction: Building a Text-Based RPG App with Streamlit

## Overview
You are assisting in building a Streamlit-based web app for a text-based role-playing game (RPG). The app features a "dungeon master" AI called **StoryOS** that responds to player inputs in turns. Scenarios can be anything (e.g., fantasy dungeon crawl, university life with romances, etc.), not limited to D&D-style fantasy.

Key features:
- User authentication with persistence.
- MongoDB for data storage.
- Menu for starting/loading games, viewing/editing scenarios, and (for admins) editing the system prompt.
- Chat-based game interface powered by LLMs for generating responses.
- Efficient prompt management to handle long conversations (using summaries and last 5 chats).

The app must follow the exact specifications below. Generate code modularly (e.g., separate Python files for auth, database utils, LLM utils, UI components). Use Streamlit for the UI, and ensure session state is used for persistence within sessions.

## Technologies
- **Frontend/Backend**: Streamlit (use `streamlit` library for UI, forms, buttons, chat interfaces).
- **Database**: MongoDB (use `pymongo` library). Collections:
  - `users`: Store user data (e.g., username, password hash, role: 'admin' or 'user').
  - `scenarios`: Store scenario JSON documents (e.g., fields like `name`, `description`, `initial_state`).
  - `saved_games`: Store saved game states (e.g., game ID, user ID, scenario ID, current summary).
  - `chats`: Store chat history (e.g., game ID, message list with sender: 'player' or 'StoryOS', content, timestamp).
  - `system_prompts`: Store system prompts (e.g., documents with `content` and `active: true/false`).
- **LLMs**: Use an LLM utility class to access two models:
  - Grok-4: For creative feedback (e.g., generating StoryOS responses).
  - Grok-3-mini: For quick tasks (e.g., updating summaries).
  - Implement the utility class with API calls (assume a library like `groq` or similar for Grok models; handle API keys securely via Streamlit secrets).
- **Other**: Use `streamlit.session_state` for remembering login across page reloads. Hash passwords (e.g., with `hashlib`).

## Database Schema
Define these collections in MongoDB:
- **users**:
  - `_id`: ObjectId
  - `user_id`: string (unique)
  - `password_hash`: string
  - `role`: string ('admin' or 'user')
- **scenarios**:
```
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StoryOS Scenario Schema",
  "type": "object",
  "properties": {
    "scenario_id": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "description": {
      "type": "string"
    },
    "dungeon_master_behaviour": {
      "type": "string"
    },
    "initial_location": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "player_name": {
      "type": "string"
    },
    "role": {
      "type": "string"
    },
    "setting": {
      "type": "string"
    },
    "version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"
    }
  },
  "required": [
    "scenario_id",
    "author",
    "created_at",
    "description",
    "dungeon_master_behaviour",
    "initial_location",
    "name",
    "player_name",
    "role",
    "setting",
    "version"
  ],
  "additionalProperties": false
}
```

- **active_game_sessions**:
```
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StorySummary",
  "type": "object",
  "properties": {
    "created_at": { "type": "string", "format": "date-time" },
    "last_updated": { "type": "string", "format": "date-time" },
    "user_id": { "type": "string" },
    "scenario_id": { "type": "string" },
    "game_session_id": { "type": "integer" },

    "timeline": {
      "type": "array",
      "items": {
        "type": "object",
        "title": "StoryEvent",
        "properties": {
          "datetime": { "type": "string", "format": "date-time" },
          "event_title": { "type": "string" },
          "event_description": { "type": "string" }
        },
        "required": ["datetime", "event_title", "event_description"]
      }
    },

    "character_summaries": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "title": "CharacterStory",
        "properties": {
          "character_story": { "type": "string" }
        },
        "required": ["character_story"]
      }
    },

    "world_state": { "type": "string" },
    "current_scenario": { "type": "string" }
  },
  "required": [
    "created_at",
    "last_updated",
    "user_id",
    "scenario_id",
    "game_session_id",
    "timeline",
    "character_summaries",
    "world_state",
    "current_scenario"
  ]
}
```

- **chats**:
  - `_id`: ObjectId
  - `game_session_id`: ObjectId (reference to active_game_sessions)
  - `messages`: array of objects (e.g., `{sender: 'player' or 'StoryOS', content: string, timestamp: datetime}`)
- **system_prompts**:
```
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StoryOS System Prompt Schema",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1
    },
    "content": {
      "type": "string",
      "description": "Markdown/long-form role definition"
    },
    "version": {
      "type": "string",
      "description": "Semantic version",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"
    },
    "active": {
      "type": "boolean"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "name",
    "content",
    "version",
    "active",
    "created_at",
    "updated_at"
  ],
  "additionalProperties": false
}
```

## App Flow and UI
### 1. Login System
- On app load, check if logged in via `streamlit.session_state` (e.g., `if 'user' not in st.session_state:`).
- Display a login form (username, password).
- On first run: Check if `users` collection is empty. If yes, prompt for admin username/password, create the user with role 'admin', and store hashed password.
- Authenticate: Hash input password and compare to stored hash. On success, store user in session state.
- Login persists across sessions (use session state; for multi-tab persistence, consider cookies or local storage via Streamlit extras if needed).

### 2. Main Menu (After Login)
Display a sidebar or selectbox with these options:
1. **Start a New Game**
   - Prompt user to select a scenario from `scenarios` collection (display list of scenario names).
   - Show a "Start Game" button.
   - On click: Initialize a new document in `saved_games` (link to user and scenario). Generate initial summary from scenario's `initial_state`. Send first message from StoryOS (derived from `initial_state`). Switch to chat view.

2. **Load a Saved Game**
   - List saved games for the user from `saved_games` (filter by user_id).
   - On selection: Load the game (summary from `saved_games`, full chat history from `chats`). Render chat view with history.

3. **See Role Playing Game Scenarios**
   - Load and display list of scenarios from `scenarios` (show JSON fields in a readable format, e.g., using `st.json` or expanders).
   - If user role == 'admin', show an "Edit" button for each scenario.
     - On edit: Display JSON fields in editable text boxes (parse JSON to form).
     - "Save" button: Convert form data back to JSON, update the document in `scenarios`.

4. **System Prompt** (Visible only if user role == 'admin')
   - Load the active system prompt (`active: true`) from `system_prompts` and display `content` in a textarea.
   - "Save" button: Update the document with new content (set `active: true`; optionally deactivate others).

### 3. Game Mechanics (Chat View)
- Switch to a chat interface (use `st.chat_message` and `st.chat_input` for player input).
- **LLM Setup**: Define an `LLMUtility` class with methods like `call_grok4(prompt)` and `call_grok3mini(prompt)` for API interactions. Support streaming for Grok-4 responses (e.g., using generator-based API calls and `st.write_stream`).
- **Starting a New Game**:
  - First message: From StoryOS, based on scenario's `initial_state`.
  - Generate initial summary using LLM (e.g., call Grok-4 to summarize initial_state).
  - Save to `saved_games` and add first message to `chats`.

- **Player Interaction Loop**:
  - Player enters message via chat input.
  - Construct prompt for StoryOS response:
    - System prompt (loaded from active `system_prompts`).
    - Current summary (from `saved_games`).
    - Last 5 chat interactions (from `chats` for this game).
  - Call Grok-4 to generate the StoryOS response (this response contains only the reply to the player's input).
  - Stream the Grok-4 response back to the chat screen (e.g., as a StoryOS message using Streamlit's streaming features like `st.write_stream`).
  - Once the response is fully streamed and complete:
    - Update `chats`: Append player message and the full StoryOS response.
    - Update summary: Make another call to Grok-4, passing the current summary, the most recent player input, and the LLM response. Instruct Grok-4 to incorporate this new information into an updated summary (e.g., prompt: "Update the following game summary by adding the recent player input and AI response: [current summary] [player input] [AI response]").
    - Save the updated summary to `saved_games`.

- **Loading an Existing Game**:
  - Load full chat history from `chats` and render in chat view (e.g., loop through messages and use `st.chat_message`).
  - Load summary from `saved_games` and active system prompt.
  - Resume from there: Player inputs continue the loop as above.

- **Efficiency**: Ensure prompts don't grow too large by always using summary + last 5 chats. Save after each turn (chats and summary).

## Additional Implementation Notes
- **Security**: Hash passwords. Validate inputs. Ensure admin-only features check role.
- **Error Handling**: Handle MongoDB connections, LLM API errors, empty collections gracefully (e.g., with Streamlit warnings).
- **Streamlit Best Practices**: Use `st.sidebar` for menus, `st.form` for inputs, `st.session_state` for state management.
- **Modular Code Structure**:
  - `app.py`: Main Streamlit entrypoint (handles routing based on menu).
  - `auth.py`: Login and user management functions.
  - `db_utils.py`: MongoDB connection and CRUD functions.
  - `llm_utils.py`: LLMUtility class with model calls.
  - `game_logic.py`: Functions for prompt construction, summary updates, chat handling.
- **Testing**: Include placeholders for API keys in `secrets.toml`. Test flows like first-time admin creation, game saving/loading.

Generate code step-by-step based on this spec. If a section is unclear, ask for clarification in comments.

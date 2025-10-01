# StoryOS

**An AI-powered interactive storytelling platform where you become the protagonist of dynamic, evolving narratives.**

StoryOS combines cutting-edge AI language models with real-time visualization to create immersive text-based adventures. Step into pre-built scenarios or create your own, where your choices shape the story and AI brings the world to life.

---

## 🎮 What is StoryOS?

StoryOS is a web-based platform that lets you experience interactive stories powered by artificial intelligence. Think of it as a dungeon master that never sleeps—an AI narrator that responds to your actions in real-time, creating unique story paths based on your decisions.

### Features

- **📖 Dynamic Storytelling**: AI-powered narratives that adapt to your choices
- **🎨 AI Visualization**: Generate scene illustrations with Kling.ai integration
- **🎭 Multiple Scenarios**: Pre-built story worlds or create your own
- **💬 Real-time Interaction**: WebSocket-powered streaming responses
- **👥 User Management**: Role-based access with admin controls
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices

---

## 🚀 Getting Started as a User

### 1. Registration

1. Navigate to the StoryOS web application
2. Click **Register** on the login page
3. Enter your username and password
4. Your account will be created with "pending" status
5. Wait for an administrator to approve your account

### 2. First Login

Once approved by an admin:
1. Enter your credentials on the login page
2. You'll be taken to the main menu

### 3. Starting a Story

1. Click **Scenarios** to browse available stories
2. Select a scenario to view its description and setting
3. Click **Back** then **Start New Game**
4. Choose your scenario from the list
5. The story begins!

### 4. Playing the Game

- **Reading**: Story text streams in real-time in the chat window
- **Responding**: Type your actions in the text box at the bottom
- **Visualizing**: Click "Visualize" buttons to generate AI artwork of scenes
- **History**: Scroll up to review previous story beats

### 5. Managing Sessions

- View all your game sessions from the main menu
- Resume any previous session
- Each session maintains its own story state and history

---

## 🔧 Admin Guide

### Admin Panel Access

Admins have access to additional features via the **Admin Panel** button in the main menu.

### User Management

**Approving New Users:**
1. Go to Admin Panel
2. View the "Pending User Approvals" section
3. Click **Approve as User** for regular access
4. Click **Approve as Admin** to grant admin privileges

### Scenario Management

**Viewing Scenarios:**
1. Navigate to **Scenarios** from main menu
2. Admins can see all scenarios (public and private)

**Creating Scenarios:**
1. Click **Create New** in the Scenarios page
2. Fill in required fields:
   - **Scenario ID**: Unique identifier (e.g., `medieval_quest`)
   - **Name**: Display name
   - **Description**: What the scenario is about (supports markdown)
   - **Setting**: The world/time period (supports markdown)
   - **Dungeon Master Behaviour**: How the AI should narrate (supports markdown)
   - **Player Name**: Default character name
   - **Role**: Character role/class
   - **Initial Location**: Starting point of the story
   - **Visibility**: `public` (all users) or `private` (creator only)
3. Click **Create**

**Editing Scenarios:**
1. Select any scenario
2. Click **Edit**
3. Modify fields as needed
4. Click **Save**

**Cloning Scenarios:**
- When editing a scenario you don't own, it creates a copy
- The copy is assigned to you with " - cloned by {username}" appended to the name

### System Prompt Management

**Viewing System Prompts:**
1. Go to Admin Panel
2. Scroll to "System Prompts" section
3. View both story and visualization prompts

**Editing Prompts:**
1. Click **Edit** on either prompt
2. Modify the content (supports markdown)
3. Click **Save Changes**

**Prompt Types:**
- **Story System Prompt**: Instructions for the AI dungeon master
- **Visualization System Prompt**: Instructions for generating scene images

### Monitoring

The Admin Panel displays real-time statistics:
- **Users**: Total registered users
- **Scenarios**: Available scenarios
- **Active Sessions**: Currently running games

---

## 💻 Technical Overview

### Architecture

StoryOS uses a modern web stack:

```
┌─────────────────┐
│  React Frontend │ (Vite, TypeScript, Redux Toolkit)
│  Port 5173      │
└────────┬────────┘
         │ HTTP/WS
         ▼
┌─────────────────┐
│ FastAPI Backend │ (Python 3.11, Uvicorn)
│  Port 8000      │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌─────────┐ ┌──────┐ ┌────────┐ ┌────────┐
│ MongoDB │ │ xAI  │ │Kling.ai│ │ Redis  │
│ Atlas   │ │ API  │ │  API   │ │(unused)│
└─────────┘ └──────┘ └────────┘ └────────┘
```

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- Redux Toolkit for state management
- React Router for navigation
- ReactMarkdown for formatted text
- Vite for building and development

**Backend:**
- FastAPI for REST API and WebSocket support
- Pydantic for data validation
- PyMongo for MongoDB integration
- JWT for authentication
- OpenAI SDK for xAI integration

**Database:**
- MongoDB Atlas for data persistence
  - Collections: users, scenarios, game_sessions, chats, system_prompts, visualization_tasks

**AI Services:**
- xAI (Grok) for story generation
- Kling.ai for image generation

### Project Structure

```
storyos2/
├── backend/
│   ├── api/                  # FastAPI routes and middleware
│   │   ├── routers/          # API endpoints (auth, game, scenarios, admin, websocket)
│   │   ├── dependencies.py   # Dependency injection
│   │   └── main.py           # Application entry point
│   ├── config/               # Settings and environment variables
│   ├── core/                 # Game logic and story generation
│   ├── models/               # Pydantic models
│   ├── services/             # Business logic layer
│   └── utils/                # Database, LLM, and helper utilities
├── frontend/
│   ├── public/               # Static assets (favicons, etc.)
│   └── src/
│       ├── components/       # React components (ChatHistory, Tooltip)
│       ├── pages/            # Page components (Login, Game, Scenarios, AdminPanel)
│       ├── store/            # Redux store and slices
│       ├── hooks/            # Custom React hooks
│       └── styles.css        # Global styles
├── data/                     # Scenario templates and system prompts
├── assets/                   # Images and branding
├── requirements.txt          # Python dependencies
└── docker-compose.yml        # Container orchestration
```

### Key Features Implementation

**Real-time Story Streaming:**
- WebSocket connection at `/ws/game/{session_id}`
- Server streams LLM responses token by token
- Client displays streaming text with markdown formatting

**Visualization Pipeline:**
1. Story response generates 3 visualization prompts
2. Prompts are attached to the latest message
3. User clicks "Visualize" button
4. Backend calls Kling.ai API to generate image
5. Task polling checks for completion
6. Image URL is saved and displayed

**User Authentication:**
- JWT-based authentication
- Role-based access control (admin, user, pending)
- First registered user automatically becomes admin
- New users require admin approval

**Session Management:**
- Each game session maintains:
  - World state summary
  - Character summaries
  - Event history
  - Chat messages with visualization prompts

---

## 🛠️ Developer Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- MongoDB (local or Atlas)
- Git

### Installation

**1. Clone the repository:**
```bash
git clone <repository-url>
cd storyos2
```

**2. Backend setup:**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**3. Frontend setup:**
```bash
cd frontend
npm install
cd ..
```

**4. Environment configuration:**

Create `.env` in the root directory:
```bash
# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_DATABASE_NAME=storyos

# AI Services
XAI_API_KEY=your_xai_api_key
KLING_ACCESS_KEY=your_kling_access_key
KLING_SECRET_KEY=your_kling_secret_key
KLING_JWT_TTL=3600

# Authentication
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=43200

# CORS
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:5173

# Logging
STORYOS_LOG_LEVEL=INFO
STORYOS_LOG_TO_FILE=true
ENABLE_DEBUG_FILE_LOGGING=false
```

Create `frontend/.env`:
```bash
VITE_BACKEND_API_URL=http://localhost:8000/api
VITE_BACKEND_WEBSOCKET_URL=ws://localhost:8000/ws
```

**5. Run the application:**

Terminal 1 (Backend):
```bash
source .venv/bin/activate
uvicorn backend.api.main:app --reload --port 8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Access the application at `http://localhost:5173`

### Running Tests

```bash
pytest backend/tests/
```

### Building for Production

```bash
# Build frontend
cd frontend
npm run build
cd ..

# The built files in frontend/dist/ will be served by the FastAPI backend
```

---

## 📦 Deployment

See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for detailed deployment instructions to Azure App Service.

Quick deploy:
```bash
./deploy.sh  # Builds frontend
# Then deploy to your hosting platform
```

---

## 🔑 API Reference

### Authentication

**POST /api/auth/register**
- Register a new user account
- Body: `{ username, password, role }`
- Returns: `{ user_id, role }`

**POST /api/auth/login**
- Login with credentials
- Body: OAuth2 form (username, password)
- Returns: `{ access_token, token_type, user_role }`

**GET /api/auth/me**
- Get current user info
- Headers: `Authorization: Bearer {token}`
- Returns: `{ user_id, role }`

### Game Sessions

**POST /api/game/sessions**
- Create a new game session
- Body: `{ scenario_id }`
- Returns: `{ session_id }`

**GET /api/game/sessions**
- List user's game sessions
- Returns: Array of session objects

**GET /api/game/sessions/{session_id}**
- Get session details and chat history
- Returns: `{ session, messages }`

**WS /ws/game/{session_id}?token={jwt}**
- WebSocket for real-time gameplay
- Send: `{ type: "player_input", content: "your action" }`
- Receive: Streaming story responses

### Scenarios

**GET /api/scenarios**
- List available scenarios
- Returns: Array of scenario objects

**POST /api/scenarios**
- Create a new scenario (admin or user)
- Body: Scenario object
- Returns: Created scenario

**PUT /api/scenarios/{scenario_id}**
- Update a scenario (admin or owner)
- Body: Updated fields
- Returns: Updated scenario

### Admin

**GET /api/admin/stats**
- Get system statistics (admin only)
- Returns: `{ users, scenarios, active_sessions }`

**GET /api/admin/users/pending**
- List pending user approvals (admin only)
- Returns: Array of pending users

**PUT /api/admin/users/{user_id}/role**
- Update user role (admin only)
- Body: `{ role }`
- Returns: Updated user

**GET /api/admin/system-prompts**
- Get system prompts (admin only)
- Returns: `{ story_prompt, visualization_prompt }`

**PUT /api/admin/system-prompts/story**
- Update story system prompt (admin only)
- Body: `{ content }`
- Returns: Updated prompt

**PUT /api/admin/system-prompts/visualization**
- Update visualization system prompt (admin only)
- Body: `{ content }`
- Returns: Updated prompt

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 🆘 Support

For issues and questions:
- Check the [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for deployment issues
- Review logs in `logs/` directory (if `ENABLE_DEBUG_FILE_LOGGING=true`)
- Check MongoDB Atlas logs for database issues
- Review browser console for frontend errors

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [React](https://react.dev/) and [Vite](https://vitejs.dev/)
- AI by [xAI](https://x.ai/)
- Image generation by [Kling.ai](https://klingai.com/)
- Database by [MongoDB Atlas](https://www.mongodb.com/atlas)

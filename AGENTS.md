Migrate the streamlit code base to a regular reactjs/python fe/be stack.  Follow the instructions in the report below to implement this:

# Migration Report: StoryOS v2 from Streamlit to React/FastAPI Stack

## Executive Summary

This report outlines a comprehensive migration strategy to transform StoryOS v2 from a Streamlit-based application to a modern React/TypeScript frontend with FastAPI backend architecture. This migration will provide better control flow, improved performance, and a more maintainable codebase.

## Current Architecture Analysis

### Streamlit Limitations Identified
1. **Control Flow Issues**: Streamlit's rerun mechanism creates inefficient update cycles
2. **UI Restrictions**: Limited customization of UI components and layouts
3. **State Management**: Session state handling is cumbersome and prone to race conditions
4. **Real-time Updates**: Streaming responses are difficult to implement cleanly
5. **Performance**: Full page reruns for minor state changes

### Current Structure
```
storyos2/
├── app.py                 # Streamlit entry point
├── pages/                 # Streamlit page components
│   ├── game_page.py      # Game interface (heavy streaming/state)
│   ├── load_game_page.py # Session management UI
│   ├── new_game_page.py  # Game creation UI
│   ├── scenarios_page.py # Scenario management
│   └── system_prompt_page.py # Admin UI
├── game/                  # Core game logic
├── models/               # Data models
├── utils/                # Utilities and services
└── config/               # Configuration
```

## Proposed Architecture

### Technology Stack
- **Frontend**: React 18+ with TypeScript
- **Backend**: FastAPI (Python 3.11+)
- **State Management**: Redux Toolkit or Zustand
- **API Communication**: REST + WebSockets for real-time updates
- **Styling**: Tailwind CSS or Material-UI
- **Build Tool**: Vite

### New Structure
```
storyos-v3/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── routers/
│   │   │   ├── auth.py         # Auth endpoints
│   │   │   ├── game.py         # Game session endpoints
│   │   │   ├── scenarios.py    # Scenario management
│   │   │   ├── admin.py        # Admin endpoints
│   │   │   └── websocket.py    # WebSocket handlers
│   │   ├── dependencies.py     # Dependency injection
│   │   └── middleware.py       # CORS, auth middleware
│   ├── core/                   # Migrated from game/
│   ├── models/                 # Existing models + Pydantic
│   ├── services/               # Business logic layer
│   └── utils/                  # Existing utilities
├── frontend/
│   ├── src/
│   │   ├── api/               # API client layer
│   │   ├── components/        # React components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── store/            # State management
│   │   ├── types/            # TypeScript definitions
│   │   └── utils/            # Frontend utilities
│   ├── package.json
│   └── tsconfig.json
└── docker-compose.yml
```

## Migration Plan

### Phase 1: Backend API Development (2-3 weeks)

#### 1.1 Setup FastAPI Project
````python
# backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from .routers import auth, game, scenarios, admin, websocket
from .dependencies import get_settings

app = FastAPI(title="StoryOS API", version="3.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(game.router, prefix="/api/game", tags=["game"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["scenarios"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
````

#### 1.2 Convert Authentication System
````python
# backend/api/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_role: str

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Migrate from utils.auth.authenticate_user
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(user["user_id"], user["role"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_role": user["role"]
    }

@router.post("/register")
async def register(user_data: UserRegister):
    # Migrate from first-run admin creation logic
    pass
````

#### 1.3 Game Session API
````python
# backend/api/routers/game.py
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

class GameSessionCreate(BaseModel):
    scenario_id: str

class PlayerInput(BaseModel):
    session_id: str
    content: str

@router.post("/sessions")
async def create_game_session(
    data: GameSessionCreate,
    current_user = Depends(get_current_user)
):
    # Migrate from game.game_logic.create_new_game
    session_id = create_new_game(current_user["user_id"], data.scenario_id)
    if not session_id:
        raise HTTPException(status_code=400, detail="Failed to create game")
    return {"session_id": session_id}

@router.get("/sessions")
async def get_user_sessions(current_user = Depends(get_current_user)):
    # Migrate from utils.game_session_manager.get_user_game_sessions
    sessions = get_user_game_sessions(current_user["user_id"])
    return {"sessions": sessions}

@router.get("/sessions/{session_id}")
async def get_game_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    # Migrate from game.game_logic.load_game_session
    game_data = load_game_session(session_id)
    # Verify user owns this session
    if game_data["session"]["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return game_data
````

#### 1.4 WebSocket for Streaming Responses
````python
# backend/api/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

router = APIRouter()

class GameWebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    async def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)
    
    async def send_chunk(self, session_id: str, chunk: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(chunk)

manager = GameWebSocketManager()

@router.websocket("/game/{session_id}")
async def game_websocket(websocket: WebSocket, session_id: str):
    await manager.connect(session_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "player_input":
                # Process in background to allow streaming
                asyncio.create_task(
                    process_player_input_streaming(
                        session_id, 
                        message["content"],
                        manager
                    )
                )
            elif message["type"] == "initial_story":
                asyncio.create_task(
                    generate_initial_story_streaming(
                        session_id,
                        manager
                    )
                )
    
    except WebSocketDisconnect:
        await manager.disconnect(session_id)

async def process_player_input_streaming(
    session_id: str, 
    player_input: str,
    ws_manager: GameWebSocketManager
):
    # Convert generator to async streaming
    for chunk in process_player_input(session_id, player_input):
        await ws_manager.send_chunk(session_id, json.dumps({
            "type": "story_chunk",
            "content": chunk
        }))
    
    await ws_manager.send_chunk(session_id, json.dumps({
        "type": "story_complete"
    }))
````

### Phase 2: Frontend Development (3-4 weeks)

#### 2.1 React App Setup
````typescript
// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';

import Login from './pages/Login';
import MainMenu from './pages/MainMenu';
import Game from './pages/Game';
import Scenarios from './pages/Scenarios';
import LoadGame from './pages/LoadGame';
import NewGame from './pages/NewGame';
import AdminPanel from './pages/AdminPanel';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <Provider store={store}>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><MainMenu /></ProtectedRoute>} />
          <Route path="/game/:sessionId" element={<ProtectedRoute><Game /></ProtectedRoute>} />
          <Route path="/scenarios" element={<ProtectedRoute><Scenarios /></ProtectedRoute>} />
          <Route path="/load-game" element={<ProtectedRoute><LoadGame /></ProtectedRoute>} />
          <Route path="/new-game" element={<ProtectedRoute><NewGame /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute requireAdmin><AdminPanel /></ProtectedRoute>} />
        </Routes>
      </Router>
    </Provider>
  );
}
````

#### 2.2 API Client Layer
````typescript
// frontend/src/api/client.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Game API
export const gameAPI = {
  createSession: (scenarioId: string) => 
    apiClient.post('/game/sessions', { scenario_id: scenarioId }),
  
  getSession: (sessionId: string) =>
    apiClient.get(`/game/sessions/${sessionId}`),
  
  getUserSessions: () =>
    apiClient.get('/game/sessions'),
};

// WebSocket connection for game streaming
export class GameWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string;
  
  constructor(sessionId: string) {
    this.sessionId = sessionId;
  }
  
  connect(onMessage: (data: any) => void): void {
    const wsUrl = `ws://localhost:8000/ws/game/${this.sessionId}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
  }
  
  sendPlayerInput(input: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'player_input',
        content: input
      }));
    }
  }
  
  disconnect(): void {
    this.ws?.close();
  }
}
````

#### 2.3 Game Page Component
````typescript
// frontend/src/pages/Game.tsx
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { GameWebSocket } from '../api/client';
import ChatHistory from '../components/ChatHistory';
import PlayerInput from '../components/PlayerInput';
import LoadingIndicator from '../components/LoadingIndicator';

interface Message {
  sender: 'player' | 'StoryOS';
  content: string;
  timestamp: string;
}

const Game: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const wsRef = useRef<GameWebSocket | null>(null);
  
  useEffect(() => {
    if (!sessionId) return;
    
    // Load existing messages
    loadGameSession();
    
    // Connect WebSocket
    wsRef.current = new GameWebSocket(sessionId);
    wsRef.current.connect(handleWebSocketMessage);
    
    return () => {
      wsRef.current?.disconnect();
    };
  }, [sessionId]);
  
  const loadGameSession = async () => {
    try {
      const response = await gameAPI.getSession(sessionId!);
      setMessages(response.data.messages);
      
      // If no messages, request initial story
      if (response.data.messages.length === 0) {
        requestInitialStory();
      }
    } catch (error) {
      console.error('Failed to load game session:', error);
      navigate('/');
    }
  };
  
  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'story_chunk':
        setStreamingContent(prev => prev + data.content);
        break;
      
      case 'story_complete':
        if (streamingContent) {
          const newMessage: Message = {
            sender: 'StoryOS',
            content: streamingContent,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, newMessage]);
          setStreamingContent('');
        }
        setIsLoading(false);
        break;
    }
  };
  
  const handlePlayerInput = (input: string) => {
    // Add player message immediately
    const playerMessage: Message = {
      sender: 'player',
      content: input,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, playerMessage]);
    
    // Send via WebSocket
    setIsLoading(true);
    wsRef.current?.sendPlayerInput(input);
  };
  
  return (
    <div className="game-container">
      <header className="game-header">
        <h1>StoryOS - Interactive Adventure</h1>
        <button onClick={() => navigate('/')}>Back to Menu</button>
      </header>
      
      <main className="game-main">
        <ChatHistory 
          messages={messages} 
          streamingContent={streamingContent}
        />
        
        {isLoading && <LoadingIndicator message="StoryOS is crafting your fate..." />}
        
        <PlayerInput 
          onSubmit={handlePlayerInput}
          disabled={isLoading}
        />
      </main>
    </div>
  );
};
````

### Phase 3: Data Migration & Integration (1-2 weeks)

#### 3.1 State Management Migration
````typescript
// frontend/src/store/slices/authSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { authAPI } from '../../api/client';

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
}

export const login = createAsyncThunk(
  'auth/login',
  async ({ username, password }: LoginCredentials) => {
    const response = await authAPI.login(username, password);
    localStorage.setItem('auth_token', response.data.access_token);
    return response.data;
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    user: null,
    token: localStorage.getItem('auth_token'),
    isLoading: false,
    error: null,
  } as AuthState,
  reducers: {
    logout: (state) => {
      state.user = null;
      state.token = null;
      localStorage.removeItem('auth_token');
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.token = action.payload.access_token;
        // Decode user info from token
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Login failed';
      });
  },
});
````

#### 3.2 Service Layer Migration

Create service wrappers to maintain business logic:

````python
# backend/services/game_service.py
from typing import Generator, Optional
import asyncio

class GameService:
    def __init__(self, db_manager, llm_utility):
        self.db = db_manager
        self.llm = llm_utility
    
    async def create_game_session(
        self, 
        user_id: str, 
        scenario_id: str
    ) -> Optional[str]:
        """Async wrapper for game creation"""
        # Migrate logic from game.game_logic.create_new_game
        return await asyncio.to_thread(
            create_new_game, 
            user_id, 
            scenario_id
        )
    
    async def process_player_input_async(
        self,
        session_id: str,
        player_input: str
    ) -> AsyncGenerator[str, None]:
        """Convert sync generator to async"""
        loop = asyncio.get_event_loop()
        
        # Run sync generator in thread pool
        def sync_gen():
            for chunk in process_player_input(session_id, player_input):
                yield chunk
        
        gen = sync_gen()
        while True:
            try:
                chunk = await loop.run_in_executor(None, next, gen)
                yield chunk
            except StopIteration:
                break
````

### Phase 4: Testing & Deployment (1 week)

#### 4.1 API Testing
````python
# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_create_game_session():
    # Login first
    response = client.post("/api/auth/login", data={
        "username": "test_user",
        "password": "test_pass"
    })
    token = response.json()["access_token"]
    
    # Create game session
    response = client.post(
        "/api/game/sessions",
        json={"scenario_id": "test_scenario"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert "session_id" in response.json()
````

#### 4.2 Docker Deployment
````yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mongodb://mongodb:27017/storyos
      - XAI_API_KEY=${XAI_API_KEY}
    depends_on:
      - mongodb
      - redis
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000/api
    depends_on:
      - backend
  
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

volumes:
  mongo_data:
````

## Migration Benefits

### Performance Improvements
- **Eliminated full page reruns**: React only updates changed components
- **Efficient state management**: Redux/Zustand provides predictable state updates
- **True streaming**: WebSockets enable real-time streaming without hacks
- **Optimized API calls**: Only fetch needed data, implement caching

### Developer Experience
- **Clear separation of concerns**: Frontend/backend split
- **Type safety**: TypeScript catches errors at compile time
- **Better debugging**: React DevTools and Redux DevTools
- **Modular architecture**: Easier to test and maintain

### User Experience
- **Responsive UI**: No page flickers or reloads
- **Real-time updates**: Smooth streaming of AI responses
- **Better error handling**: Graceful error boundaries
- **Improved accessibility**: Full control over HTML structure

## Migration Timeline

- **Week 1-2**: Backend API development
- **Week 3-4**: Core frontend development
- **Week 5-6**: Advanced features and WebSocket integration
- **Week 7**: Testing and bug fixes
- **Week 8**: Deployment and monitoring setup

## Key Considerations

1. **Data Migration**: Existing MongoDB data remains compatible
2. **Authentication**: JWT tokens replace session-based auth
3. **File Uploads**: Use multipart form data instead of Streamlit's file_uploader
4. **Deployment**: Requires separate hosting for frontend/backend
5. **Development Workflow**: Need to run both frontend and backend during development

## Conclusion

This migration from Streamlit to React/FastAPI will result in a more scalable, performant, and maintainable application. While it requires significant initial effort, the benefits in terms of user experience, developer productivity, and system flexibility make it a worthwhile investment for StoryOS v2's future growth.
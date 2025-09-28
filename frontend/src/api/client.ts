import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_BACKEND_API_URL ?? 'http://localhost:8000/api';
const WS_BASE_URL = import.meta.env.VITE_BACKEND_WEBSOCKET_URL ?? 'ws://localhost:8000/ws';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: (username: string, password: string) => {
    const params = new URLSearchParams();
    params.set('grant_type', 'password');
    params.set('username', username);
    params.set('password', password);
    return apiClient.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  register: (username: string, password: string, role: string) =>
    apiClient.post('/auth/register', { username, password, role }),
  me: () => apiClient.get('/auth/me')
};

export const gameAPI = {
  createSession: (scenarioId: string) =>
    apiClient.post('/game/sessions', { scenario_id: scenarioId }),
  getUserSessions: () => apiClient.get('/game/sessions'),
  getSession: (sessionId: string) => apiClient.get(`/game/sessions/${sessionId}`),
  visualizePrompt: (sessionId: string, messageId: string, prompt: string) =>
    apiClient.post(`/game/sessions/${sessionId}/messages/${messageId}/visualize`, {
      prompt
    })
};

export const scenarioAPI = {
  list: () => apiClient.get('/scenarios'),
  get: (scenarioId: string) => apiClient.get(`/scenarios/${scenarioId}`)
};

export class GameWebSocket {
  private ws: WebSocket | null = null;
  private readonly sessionId: string;
  private readonly token: string;
  private queue: string[] = [];

  constructor(sessionId: string, token: string) {
    this.sessionId = sessionId;
    this.token = token;
  }

  connect(onMessage: (data: any) => void, onClose?: () => void, onOpen?: () => void): void {
    const wsUrl = `${WS_BASE_URL}/game/${this.sessionId}?token=${this.token}`;
    this.ws = new WebSocket(wsUrl);
    this.ws.onopen = () => {
      this.flushQueue();
      if (onOpen) onOpen();
    };
    this.ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      onMessage(payload);
    };
    if (onClose) {
      this.ws.onclose = onClose;
    }
  }

  sendPlayerInput(content: string): void {
    this.enqueue(
      JSON.stringify({
        type: 'player_input',
        content
      })
    );
  }

  requestInitialStory(): void {
    this.enqueue(
      JSON.stringify({
        type: 'initial_story'
      })
    );
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
    this.queue = [];
  }

  private enqueue(payload: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(payload);
    } else {
      this.queue.push(payload);
    }
  }

  private flushQueue(): void {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      return;
    }
    while (this.queue.length > 0) {
      const payload = this.queue.shift();
      if (payload) {
        this.ws.send(payload);
      }
    }
  }
}

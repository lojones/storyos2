import axios from 'axios';

// Always use relative URLs - Vite proxy handles dev, same-origin handles production
const API_BASE_URL = '/api';
const WS_BASE_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;

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
  deleteSession: (sessionId: string) => apiClient.delete(`/game/sessions/${sessionId}`),
  visualizePrompt: (sessionId: string, messageId: string, prompt: string) =>
    apiClient.post(`/game/sessions/${sessionId}/messages/${messageId}/visualize`, {
      prompt
    }),
  updateGameSpeed: (sessionId: string, gameSpeed: number) =>
    apiClient.patch(`/game/sessions/${sessionId}/game-speed`, { game_speed: gameSpeed })
};

export const scenarioAPI = {
  list: () => apiClient.get('/scenarios/'),
  get: (scenarioId: string) => apiClient.get(`/scenarios/${scenarioId}`),
  update: (scenarioId: string, data: Record<string, any>) =>
    apiClient.put(`/scenarios/${scenarioId}`, data),
  create: (data: Record<string, any>) =>
    apiClient.post('/scenarios/', data)
};

export const adminAPI = {
  getPendingUsers: () => apiClient.get('/admin/users/pending'),
  updateUserRole: (userId: string, role: string) =>
    apiClient.put(`/admin/users/${userId}/role`, { role }),
  getSystemPrompts: () => apiClient.get('/admin/system-prompts'),
  updateStoryPrompt: (content: string) =>
    apiClient.put('/admin/system-prompts/story', { content }),
  updateVisualizationPrompt: (content: string) =>
    apiClient.put('/admin/system-prompts/visualization', { content })
};

export class GameWebSocket {
  private ws: WebSocket | null = null;
  private readonly sessionId: string;
  private readonly token: string;
  private queue: string[] = [];
  private onMessageCallback: ((data: any) => void) | null = null;
  private onCloseCallback: (() => void) | undefined;
  private onOpenCallback: (() => void) | undefined;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private isManualDisconnect = false;

  constructor(sessionId: string, token: string) {
    this.sessionId = sessionId;
    this.token = token;
  }

  connect(onMessage: (data: any) => void, onClose?: () => void, onOpen?: () => void): void {
    this.onMessageCallback = onMessage;
    this.onCloseCallback = onClose;
    this.onOpenCallback = onOpen;
    this.isManualDisconnect = false;
    this.createWebSocket();
  }

  private createWebSocket(): void {
    const wsUrl = `${WS_BASE_URL}/game/${this.sessionId}?token=${this.token}`;
    console.log('[WebSocket] Connecting to:', wsUrl);

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('[WebSocket] Connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.flushQueue();
      if (this.onOpenCallback) this.onOpenCallback();
    };

    this.ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (this.onMessageCallback) {
        this.onMessageCallback(payload);
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
    };

    this.ws.onclose = (event) => {
      console.log('[WebSocket] Closed:', event.code, event.reason);
      this.stopHeartbeat();

      // Don't reconnect if it was a manual disconnect or max attempts reached
      if (!this.isManualDisconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect();
      } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('[WebSocket] Max reconnect attempts reached');
        if (this.onCloseCallback) this.onCloseCallback();
      } else if (this.onCloseCallback) {
        this.onCloseCallback();
      }
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 30000); // Exponential backoff, max 30s
    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.createWebSocket();
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    // Send heartbeat every 30 seconds to keep connection alive
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify({ type: 'ping' }));
        } catch (error) {
          console.error('[WebSocket] Heartbeat failed:', error);
        }
      }
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
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
    console.log('[WebSocket] Manual disconnect');
    this.isManualDisconnect = true;
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    this.ws?.close();
    this.ws = null;
    this.queue = [];
  }

  private enqueue(payload: string): void {
    // Check if connection is open
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(payload);
        console.log('[WebSocket] Sent:', payload.substring(0, 100));
      } catch (error) {
        console.error('[WebSocket] Send failed:', error);
        this.queue.push(payload);
      }
    } else if (this.ws?.readyState === WebSocket.CONNECTING) {
      // Connection in progress, queue the message
      console.log('[WebSocket] Connection in progress, queueing message');
      this.queue.push(payload);
    } else {
      // Connection closed, queue and attempt reconnect
      console.log('[WebSocket] Connection closed, queueing message and reconnecting');
      this.queue.push(payload);
      if (!this.isManualDisconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect();
      }
    }
  }

  private flushQueue(): void {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      return;
    }
    console.log(`[WebSocket] Flushing ${this.queue.length} queued messages`);
    while (this.queue.length > 0) {
      const payload = this.queue.shift();
      if (payload) {
        try {
          this.ws.send(payload);
        } catch (error) {
          console.error('[WebSocket] Failed to send queued message:', error);
          // Put it back at the front
          this.queue.unshift(payload);
          break;
        }
      }
    }
  }

  getConnectionState(): string {
    if (!this.ws) return 'DISCONNECTED';
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'CONNECTING';
      case WebSocket.OPEN: return 'OPEN';
      case WebSocket.CLOSING: return 'CLOSING';
      case WebSocket.CLOSED: return 'CLOSED';
      default: return 'UNKNOWN';
    }
  }
}

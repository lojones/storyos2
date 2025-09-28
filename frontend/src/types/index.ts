export interface AuthUser {
  userId: string;
  role: string;
}

export interface AuthState {
  user: AuthUser | null;
  token: string | null;
  role: string | null;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface Message {
  sender: 'player' | 'StoryOS';
  content: string;
  timestamp: string;
  messageId?: string;
  visualPrompts?: Record<string, string>;
}

export interface StreamingMessage extends Message {
  status?: 'streaming' | 'complete';
}

export interface GameSessionSummary {
  _id: string;
  scenario_id: string;
  user_id: string;
  last_updated?: string;
  name?: string;
}

export interface GameSessionPayload {
  session: {
    id?: string;
    user_id: string;
    scenario_id: string;
    last_scene: string;
    world_state: string;
  };
  messages: Array<{
    sender: string;
    content: string;
    timestamp?: string;
    message_id?: string;
  }>;
}

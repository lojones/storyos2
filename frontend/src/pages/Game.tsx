import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { gameAPI, GameWebSocket } from '../api/client';
import ChatHistory from '../components/ChatHistory';
import LoadingIndicator from '../components/LoadingIndicator';
import PlayerInput from '../components/PlayerInput';
import { useAuth } from '../hooks/useAuth';
import { Message } from '../types';

const LOADING_MESSAGES = [
  "The universe is aligning the threads of fate… please wait.",
  "Your choices ripple across unseen realms… hold steady.",
  "The dungeon master consults the ancient tomes… patience, traveler.",
  "Destiny is being rewritten in real time… wait a moment.",
  "Hidden dice are rolling in the shadows… please stand by.",
  "The world stirs, waiting for your next move… hold fast.",
  "Echoes of possibility converge into reality… wait here.",
  "A storysmith hammers out the next moment of legend… please wait.",
  "The cosmos weighs the balance of your decisions… just a moment.",
  "Your path is being woven into the grand tapestry… patience, adventurer.",
  "The fates whisper among themselves… please wait.",
  "The tapestry of destiny is being woven… hold steady.",
  "Shadows gather before the tale continues… wait a moment.",
  "The dice tumble in the void of chance… patience, adventurer.",
  "The realm holds its breath, awaiting your path… stand by.",
  "Ancient tomes turn their pages to your story… please wait.",
  "The stars align to shape your next choice… hold fast.",
  "Unseen hands set the stage for what's to come… wait here.",
  "The echoes of possibility are resolving into truth… just a moment.",
  "The wheel of fate creaks forward slowly… wait, traveler."
];

const Game: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { token } = useAuth();

  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState<string>('');
  const [sessionHeadline, setSessionHeadline] = useState<string>('');
  const [visualizingKey, setVisualizingKey] = useState<string | null>(null);
  const [visualizationError, setVisualizationError] = useState<string | null>(null);
  const [summaryExpanded, setSummaryExpanded] = useState(false);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [gameSpeed, setGameSpeed] = useState(4);
  const hasLoadedOnceRef = useRef(false);
  const loadingMessageIndexRef = useRef(0);

  const wsRef = useRef<GameWebSocket | null>(null);
  const requestedSessionsRef = useRef<Set<string>>(
    (globalThis as { __storyosInitialRequests?: Set<string> }).__storyosInitialRequests ??
      new Set<string>()
  );
  const handleWebsocketMessageRef = useRef<(payload: any) => void>(() => {});

  useEffect(() => {
    (globalThis as { __storyosInitialRequests?: Set<string> }).__storyosInitialRequests =
      requestedSessionsRef.current;
  }, []);

  const normaliseMessages = useCallback((rawMessages: Array<any>): Message[] => {
    return rawMessages.map((message) => {
      const messageId =
        message.message_id ?? message.messageId ?? message.messageID ?? undefined;
      const promptsSource =
        message.visual_prompts ?? message.visualPrompts ?? undefined;
      const visualPrompts =
        promptsSource && typeof promptsSource === 'object'
          ? Object.fromEntries(
              Object.entries(
                promptsSource as Record<string, string | null | undefined>
              ).map(([prompt, url]) => [prompt, url ?? ''])
            )
          : undefined;

      return {
        sender: message.sender === 'player' ? 'player' : 'StoryOS',
        content: message.content,
        timestamp: message.timestamp ?? new Date().toISOString(),
        messageId,
        visualPrompts,
      };
    });
  }, []);

  const loadSession = useCallback(async () => {
    if (!sessionId) return;

    // Only show loading spinner on the first load
    if (!hasLoadedOnceRef.current) {
      setIsLoadingSession(true);
    }

    try {
      const response = await gameAPI.getSession(sessionId);
      const data = response.data;
      setSessionHeadline(data.session?.last_scene ?? 'Interactive Narrative');
      setMessages(normaliseMessages(data.messages ?? []));
      setVisualizationError(null);

      // Load game speed from session data
      if (data.session?.game_speed !== undefined) {
        setGameSpeed(data.session.game_speed);
      }

      if (
        (data.messages ?? []).length === 0 &&
        !requestedSessionsRef.current.has(sessionId)
      ) {
        requestedSessionsRef.current.add(sessionId);
        setIsLoading(true);
        // Use the first loading message for initial story
        const currentMessage = LOADING_MESSAGES[loadingMessageIndexRef.current];
        setLoadingMessage(currentMessage);
        loadingMessageIndexRef.current = (loadingMessageIndexRef.current + 1) % LOADING_MESSAGES.length;
        wsRef.current?.requestInitialStory();
      }

    } catch (error) {
      console.error('Failed to load game session', error);
      navigate('/');
    } finally {
      // Only turn off loading spinner after first load
      if (!hasLoadedOnceRef.current) {
        setIsLoadingSession(false);
        hasLoadedOnceRef.current = true;
      }
    }
  }, [sessionId, normaliseMessages, navigate]);

  const handleWebsocketMessage = useCallback(
    (payload: any) => {
      switch (payload.type) {
        case 'status_update':
          // Ignore backend status updates - we use our own cycling messages
          break;
        case 'story_chunk':
          setStreamingContent((prev) => prev + payload.content);
          break;
        case 'story_complete':
          setStreamingContent((prev) => {
            if (prev) {
              setMessages((prior) => [
                ...prior,
                {
                  sender: 'StoryOS',
                  content: prev,
                  timestamp: new Date().toISOString(),
                },
              ]);
            }
            return '';
          });
          setIsLoading(false);
          setLoadingMessage('');
          void loadSession();
          break;
        case 'visual_prompts_ready':
          // Reload session to get the updated visual prompts
          void loadSession();
          break;
        case 'error':
          setStreamingContent('');
          setIsLoading(false);
          setLoadingMessage('');
          setVisualizationError(
            typeof payload.message === 'string'
              ? payload.message
              : 'Visualization stream encountered an error.'
          );
          break;
        default:
          break;
      }
    },
    [loadSession]
  );

  // Update the ref whenever the callback changes
  useEffect(() => {
    handleWebsocketMessageRef.current = handleWebsocketMessage;
  }, [handleWebsocketMessage]);

  // Load session data (separate from WebSocket connection)
  useEffect(() => {
    if (!sessionId) return;
    void loadSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  // Setup WebSocket connection
  useEffect(() => {
    if (!sessionId || !token) return;

    // Prevent duplicate connections (important for React StrictMode in dev)
    if (wsRef.current) {
      console.log('[Game] WebSocket already exists, skipping duplicate connection');
      return;
    }

    console.log('[Game] Creating new WebSocket connection for session:', sessionId);
    const ws = new GameWebSocket(sessionId, token);
    wsRef.current = ws;

    // Use a stable wrapper that calls the ref
    ws.connect((payload) => handleWebsocketMessageRef.current(payload), () => setIsLoading(false));

    return () => {
      console.log('[Game] Cleaning up WebSocket connection for session:', sessionId);
      // Only disconnect if this is still the active connection
      if (wsRef.current === ws) {
        ws.disconnect();
        wsRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, token]);

  const handlePlayerInput = (content: string) => {
    if (!sessionId) return;
    const playerMessage: Message = {
      sender: 'player',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, playerMessage]);
    setIsLoading(true);
    setStreamingContent('');

    // Cycle to the next loading message
    const currentMessage = LOADING_MESSAGES[loadingMessageIndexRef.current];
    setLoadingMessage(currentMessage);
    loadingMessageIndexRef.current = (loadingMessageIndexRef.current + 1) % LOADING_MESSAGES.length;

    wsRef.current?.sendPlayerInput(content);
  };

  const handleVisualize = async (messageId: string, prompt: string) => {
    if (!sessionId) return;

    setVisualizationError(null);
    const key = `${messageId}:${prompt}`;
    setVisualizingKey(key);

    try {
      await gameAPI.visualizePrompt(sessionId, messageId, prompt);
      await loadSession();
    } catch (error) {
      console.error('Visualization request failed', error);
      const detail = (error as any)?.response?.data?.detail;
      setVisualizationError(
        typeof detail === 'string' ? detail : 'Failed to generate visualization.'
      );
    } finally {
      setVisualizingKey(null);
    }
  };

  const handleGameSpeedChange = async (newSpeed: number) => {
    if (!sessionId) return;

    setGameSpeed(newSpeed);

    try {
      await gameAPI.updateGameSpeed(sessionId, newSpeed);
    } catch (error) {
      console.error('Failed to update game speed', error);
      // Optionally reload session to get the correct value
      await loadSession();
    }
  };

  if (isLoadingSession) {
    return (
      <div className="main-content" style={{ maxWidth: '960px', margin: '0 auto' }}>
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', minHeight: '80vh', alignItems: 'center', justifyContent: 'center' }}>
          <LoadingIndicator message="Loading session..." />
        </div>
      </div>
    );
  }

  return (
    <div className="main-content" style={{ maxWidth: '960px', margin: '0 auto' }}>
      <div className="panel" style={{ display: 'flex', flexDirection: 'column', minHeight: '80vh' }}>
        <div className="game-header" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h1>StoryOS Mission Console</h1>
            <button className="primary" onClick={() => navigate('/')}>Back to Main Menu</button>
          </div>
          <p
            className={summaryExpanded ? 'summary-text expanded' : 'summary-text'}
            style={{ opacity: 0.7, cursor: 'pointer', marginTop: '0.5rem' }}
            onClick={() => setSummaryExpanded(!summaryExpanded)}
          >
            {sessionHeadline || 'Live narrative channel'}
          </p>
        </div>

        {visualizationError && (
          <div style={{ color: '#f87171', marginBottom: '1rem' }}>{visualizationError}</div>
        )}

        <div className="chat-container">
          <ChatHistory
            messages={messages}
            streamingContent={streamingContent}
            onVisualize={handleVisualize}
            visualizingKey={visualizingKey}
            visualizationError={visualizationError}
          />
          {isLoading && <LoadingIndicator message={loadingMessage || "StoryOS is working…"} />}
          <PlayerInput
            onSubmit={handlePlayerInput}
            disabled={isLoading}
            gameSpeed={gameSpeed}
            onGameSpeedChange={handleGameSpeedChange}
          />
        </div>
      </div>
    </div>
  );
};

export default Game;

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { gameAPI, GameWebSocket } from '../api/client';
import ChatHistory from '../components/ChatHistory';
import LoadingIndicator from '../components/LoadingIndicator';
import PlayerInput from '../components/PlayerInput';
import { useAuth } from '../hooks/useAuth';
import { Message } from '../types';

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
  const hasLoadedOnceRef = useRef(false);

  const wsRef = useRef<GameWebSocket | null>(null);
  const requestedSessionsRef = useRef<Set<string>>(
    (globalThis as { __storyosInitialRequests?: Set<string> }).__storyosInitialRequests ??
      new Set<string>()
  );

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

      if (
        (data.messages ?? []).length === 0 &&
        !requestedSessionsRef.current.has(sessionId)
      ) {
        requestedSessionsRef.current.add(sessionId);
        setIsLoading(true);
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
          setLoadingMessage(payload.message || '');
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

  useEffect(() => {
    if (!sessionId || !token) return;

    wsRef.current = new GameWebSocket(sessionId, token);
    wsRef.current.connect(handleWebsocketMessage, () => setIsLoading(false));
    void loadSession();

    return () => {
      wsRef.current?.disconnect();
      wsRef.current = null;
    };
  }, [sessionId, token, handleWebsocketMessage, loadSession]);

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
          <h1>StoryOS Mission Console</h1>
          <div className="game-header-row">
            <p
              className={summaryExpanded ? 'summary-text expanded' : 'summary-text'}
              style={{ opacity: 0.7, cursor: 'pointer' }}
              onClick={() => setSummaryExpanded(!summaryExpanded)}
            >
              {sessionHeadline || 'Live narrative channel'}
            </p>
            <button className="primary" onClick={() => navigate('/')}>Back to Main Menu</button>
          </div>
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
          <PlayerInput onSubmit={handlePlayerInput} disabled={isLoading} />
        </div>
      </div>
    </div>
  );
};

export default Game;

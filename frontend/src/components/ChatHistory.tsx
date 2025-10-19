import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message } from '../types';
import Tooltip from './Tooltip';

interface ChatHistoryProps {
  messages: Message[];
  streamingContent?: string;
  onVisualize?: (messageId: string, prompt: string) => void;
  visualizingKey?: string | null;
  visualizationError?: string | null;
}

// Preprocess markdown to ensure lists are properly formatted
const preprocessMarkdown = (content: string): string => {
  if (!content) return content;

  // Debug: log first 200 chars and check for newlines
  console.log('Content preview:', content.substring(0, 200));
  console.log('Has newlines:', content.includes('\n'));
  console.log('Has escaped newlines:', content.includes('\\n'));

  // Replace escaped newlines if they exist
  let processed = content.replace(/\\n/g, '\n');

  // Add blank line before lines starting with "- " if not already present
  processed = processed.replace(/([^\n])\n([-*] )/g, '$1\n\n$2');

  return processed;
};

const ChatHistory: React.FC<ChatHistoryProps> = ({
  messages,
  streamingContent,
  onVisualize,
  visualizingKey,
  visualizationError,
}) => {
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const hasScrolledRef = useRef(false);
  const [progressMap, setProgressMap] = useState<Record<string, number>>({});
  const progressTimersRef = useRef<Record<string, number>>({});
  const [modalPrompt, setModalPrompt] = useState<string | null>(null);
  const chatLogRef = useRef<HTMLDivElement | null>(null);
  const [playerScrollIndicators, setPlayerScrollIndicators] = useState<Array<{ top: number; height: number }>>([]);
  const [storyScrollIndicators, setStoryScrollIndicators] = useState<Array<{ top: number; height: number }>>([]);
  const [visualizedScrollIndicators, setVisualizedScrollIndicators] = useState<Array<{ top: number; height: number }>>([]);
  const [scrollbarButtonOffset, setScrollbarButtonOffset] = useState({ top: 0, bottom: 0 });

  // Scroll to bottom only on initial load
  useEffect(() => {
    if (!hasScrolledRef.current && messages.length > 0 && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'instant' });
      hasScrolledRef.current = true;
    }
  }, [messages]);

  // Handle progress bar animation
  useEffect(() => {
    if (visualizingKey) {
      // Start progress animation for this key
      const startTime = Date.now();
      const duration = 45000; // 45 seconds
      const maxProgress = 95; // Stop at 95% if not complete

      const updateProgress = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min((elapsed / duration) * 100, maxProgress);

        setProgressMap((prev) => ({ ...prev, [visualizingKey]: progress }));

        if (progress < maxProgress) {
          progressTimersRef.current[visualizingKey] = setTimeout(updateProgress, 100);
        }
      };

      updateProgress();

      return () => {
        if (progressTimersRef.current[visualizingKey]) {
          clearTimeout(progressTimersRef.current[visualizingKey]);
          delete progressTimersRef.current[visualizingKey];
        }
      };
    }
  }, [visualizingKey]);

  // Clean up progress when visualization completes
  useEffect(() => {
    // Remove progress for keys that are no longer generating
    setProgressMap((prev) => {
      const newMap = { ...prev };
      Object.keys(newMap).forEach((key) => {
        if (key !== visualizingKey) {
          delete newMap[key];
        }
      });
      return newMap;
    });
  }, [visualizingKey]);

  // Calculate scroll indicator positions and sizes for player and story messages
  useEffect(() => {
    if (!chatLogRef.current) return;

    const calculatePositions = () => {
      const chatLog = chatLogRef.current;
      if (!chatLog) return;

      const scrollHeight = chatLog.scrollHeight;
      if (scrollHeight === 0) return;

      // Detect scrollbar button height (typically 17px on Windows)
      // We estimate this by checking if the browser is Windows and has classic scrollbars
      const hasScrollbarButtons = navigator.userAgent.includes('Windows');
      const buttonHeight = hasScrollbarButtons ? 17 : 0;
      const containerHeight = chatLog.clientHeight;

      // Calculate offset as pixels
      setScrollbarButtonOffset({
        top: buttonHeight,
        bottom: buttonHeight
      });

      // Calculate player message positions and heights
      const playerBubbles = chatLog.querySelectorAll('.chat-bubble.player');
      const playerPositions: Array<{ top: number; height: number }> = [];

      playerBubbles.forEach((bubble) => {
        const element = bubble as HTMLElement;
        const relativeTop = element.offsetTop;
        const bubbleHeight = element.offsetHeight;
        const topPercentage = (relativeTop / scrollHeight) * 100;
        const heightPercentage = (bubbleHeight / scrollHeight) * 100;
        playerPositions.push({ top: topPercentage, height: heightPercentage });
      });

      // Calculate story message positions and heights
      const storyBubbles = chatLog.querySelectorAll('.chat-bubble.story');
      const storyPositions: Array<{ top: number; height: number }> = [];

      storyBubbles.forEach((bubble) => {
        const element = bubble as HTMLElement;
        const relativeTop = element.offsetTop;
        const bubbleHeight = element.offsetHeight;
        const topPercentage = (relativeTop / scrollHeight) * 100;
        const heightPercentage = (bubbleHeight / scrollHeight) * 100;
        storyPositions.push({ top: topPercentage, height: heightPercentage });
      });

      // Calculate positions for messages with visualized images
      const visualizedBubbles = chatLog.querySelectorAll('.chat-bubble.story:has(.visualization-thumb)');
      const visualizedPositions: Array<{ top: number; height: number }> = [];

      visualizedBubbles.forEach((bubble) => {
        const element = bubble as HTMLElement;
        const relativeTop = element.offsetTop;
        const bubbleHeight = element.offsetHeight;
        const topPercentage = (relativeTop / scrollHeight) * 100;
        const heightPercentage = (bubbleHeight / scrollHeight) * 100 / 3; // One third height
        visualizedPositions.push({ top: topPercentage, height: heightPercentage });
      });

      setPlayerScrollIndicators(playerPositions);
      setStoryScrollIndicators(storyPositions);
      setVisualizedScrollIndicators(visualizedPositions);
    };

    // Calculate after render
    const timeout = setTimeout(calculatePositions, 100);

    return () => clearTimeout(timeout);
  }, [messages, streamingContent]);

  return (
    <>
      <div className="chat-log-wrapper">
        <div className="chat-log" ref={chatLogRef}>
          {messages.map((message) => (
        <div
          key={message.messageId ?? `${message.timestamp}-${message.sender}`}
          className={`chat-bubble ${message.sender === 'player' ? 'player' : 'story'}`}
        >
          {message.sender === 'StoryOS' ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {preprocessMarkdown(message.content)}
            </ReactMarkdown>
          ) : (
            <div>{message.content}</div>
          )}
          <div className="timestamp">{new Date(message.timestamp).toLocaleTimeString()}</div>
          {message.visualPrompts && Object.keys(message.visualPrompts).length > 0 && (
            <div className="visualization-action-row">
              {Object.entries(message.visualPrompts).map(([prompt, imageUrl], index) => {
                const key = `${message.messageId ?? 'message'}:${prompt}`;
                const isGenerating = visualizingKey === key;
                const progress = progressMap[key] || 0;
                const label = `Visualize ${index + 1}`;
                const hasError = visualizationError && isGenerating;

                return imageUrl ? (
                  <div key={key} className="visualization-item">
                    <a
                      href={imageUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="visualization-thumb"
                    >
                      <img src={imageUrl} alt={prompt} className="visualization-image" />
                    </a>
                    <button
                      type="button"
                      className="prompt-view-button"
                      onClick={() => setModalPrompt(prompt)}
                      title="View prompt"
                    >
                      P
                    </button>
                  </div>
                ) : (
                  <div key={key} className="visualization-item">
                    <div className="visualization-button-container">
                      {onVisualize && message.messageId && !isGenerating && (
                        <button
                          type="button"
                          className="visualization-button"
                          onClick={() => onVisualize(message.messageId!, prompt)}
                        >
                          {label}
                        </button>
                      )}
                      {isGenerating && hasError && (
                        <div className="visualization-error">
                          Visualization failed
                        </div>
                      )}
                      {isGenerating && !hasError && (
                        <div className="visualization-progress-container">
                          <div className="visualization-progress-bar">
                            <div
                              className="visualization-progress-fill"
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                          <div className="visualization-progress-text">
                            Generating... {Math.round(progress)}%
                          </div>
                        </div>
                      )}
                    </div>
                    <button
                      type="button"
                      className="prompt-view-button"
                      onClick={() => setModalPrompt(prompt)}
                      title="View prompt"
                    >
                      P
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
        ))}
        {streamingContent && (
          <div className="chat-bubble story">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {preprocessMarkdown(streamingContent)}
            </ReactMarkdown>
            <div className="timestamp">streaming…</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Scroll indicators for player messages (right side) */}
      <div
        className="scroll-indicators scroll-indicators-player"
        style={{
          top: `${scrollbarButtonOffset.top}px`,
          bottom: `${scrollbarButtonOffset.bottom}px`
        }}
      >
        {playerScrollIndicators.map((indicator, index) => (
          <div
            key={index}
            className="scroll-indicator-dot scroll-indicator-player"
            style={{ top: `${indicator.top}%`, height: `${indicator.height}%` }}
          />
        ))}
      </div>

      {/* Scroll indicators for story messages (left side) */}
      <div
        className="scroll-indicators scroll-indicators-story"
        style={{
          top: `${scrollbarButtonOffset.top}px`,
          bottom: `${scrollbarButtonOffset.bottom}px`
        }}
      >
        {storyScrollIndicators.map((indicator, index) => (
          <div
            key={index}
            className="scroll-indicator-dot scroll-indicator-story"
            style={{ top: `${indicator.top}%`, height: `${indicator.height}%` }}
          />
        ))}
      </div>

      {/* Scroll indicators for visualized messages (yellow, center) */}
      <div
        className="scroll-indicators scroll-indicators-visualized"
        style={{
          top: `${scrollbarButtonOffset.top}px`,
          bottom: `${scrollbarButtonOffset.bottom}px`
        }}
      >
        {visualizedScrollIndicators.map((indicator, index) => (
          <div
            key={index}
            className="scroll-indicator-dot scroll-indicator-visualized"
            style={{ top: `${indicator.top}%`, height: `${indicator.height}%` }}
          />
        ))}
      </div>
    </div>

      {modalPrompt && (
        <div className="prompt-modal-overlay" onClick={() => setModalPrompt(null)}>
          <div className="prompt-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="prompt-modal-header">
              <h2>Visualization Prompt</h2>
              <button
                type="button"
                className="prompt-modal-close"
                onClick={() => setModalPrompt(null)}
                aria-label="Close"
              >
                ×
              </button>
            </div>
            <div className="prompt-modal-body">
              <pre>{modalPrompt}</pre>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatHistory;

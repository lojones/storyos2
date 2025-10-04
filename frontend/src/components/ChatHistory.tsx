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

  return (
    <>
      <div className="chat-log">
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

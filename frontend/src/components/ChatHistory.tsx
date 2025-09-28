import React, { useEffect, useRef } from 'react';
import { Message } from '../types';
import Tooltip from './Tooltip';

interface ChatHistoryProps {
  messages: Message[];
  streamingContent?: string;
  onVisualize?: (messageId: string, prompt: string) => void;
  visualizingKey?: string | null;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({
  messages,
  streamingContent,
  onVisualize,
  visualizingKey,
}) => {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  return (
    <div className="chat-log">
      {messages.map((message) => (
        <div
          key={message.messageId ?? `${message.timestamp}-${message.sender}`}
          className={`chat-bubble ${message.sender === 'player' ? 'player' : 'story'}`}
        >
          <div>{message.content}</div>
          <div className="timestamp">{new Date(message.timestamp).toLocaleTimeString()}</div>
          {message.visualPrompts && Object.keys(message.visualPrompts).length > 0 && (
            <div className="visualization-action-row">
              {Object.entries(message.visualPrompts).map(([prompt, imageUrl], index) => {
                const key = `${message.messageId ?? 'message'}:${prompt}`;
                const isGenerating = visualizingKey === key;
                const label = `Visualize ${index + 1}`;

                return imageUrl ? (
                  <a
                    key={key}
                    href={imageUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="visualization-thumb"
                  >
                    <img src={imageUrl} alt={prompt} className="visualization-image" />
                  </a>
                ) : (
                  onVisualize && message.messageId && (
                    <Tooltip key={key} content={prompt}>
                      <button
                        type="button"
                        className="visualization-button"
                        onClick={() => onVisualize(message.messageId!, prompt)}
                        disabled={isGenerating}
                      >
                        {isGenerating ? 'Generating…' : label}
                      </button>
                    </Tooltip>
                  )
                );
              })}
            </div>
          )}
        </div>
      ))}
      {streamingContent && (
        <div className="chat-bubble story">
          <div>{streamingContent}</div>
          <div className="timestamp">streaming…</div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
};

export default ChatHistory;

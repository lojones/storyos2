import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message } from '../types';
import Tooltip from './Tooltip';

interface ChatHistoryProps {
  messages: Message[];
  streamingContent?: string;
  onVisualize?: (messageId: string, prompt: string) => void;
  visualizingKey?: string | null;
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
}) => {
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const hasScrolledRef = useRef(false);

  // Scroll to bottom only on initial load
  useEffect(() => {
    if (!hasScrolledRef.current && messages.length > 0 && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'instant' });
      hasScrolledRef.current = true;
    }
  }, [messages]);

  return (
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
                    <button
                      key={key}
                      type="button"
                      className="visualization-button"
                      onClick={() => onVisualize(message.messageId!, prompt)}
                      disabled={isGenerating}
                    >
                      {isGenerating ? 'Generating…' : label}
                    </button>
                  )
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
  );
};

export default ChatHistory;

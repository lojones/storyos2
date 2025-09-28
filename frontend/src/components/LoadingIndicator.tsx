import React from 'react';

interface LoadingIndicatorProps {
  message?: string;
}

const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ message = 'Loading…' }) => (
  <div className="loading-indicator">
    <span />
    <span />
    <span />
    <div>{message}</div>
  </div>
);

export default LoadingIndicator;

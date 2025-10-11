import React from 'react';

interface ProgressBarProps {
  duration?: number;
  message?: string;
  width?: string;
  height?: string;
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  duration = 120,
  message = 'This may take up to 2 minutes...',
  width = '400px',
  height = '8px'
}) => (
  <div style={{ width: '100%', maxWidth: width, marginTop: '2rem' }}>
    <div style={{
      width: '100%',
      height: height,
      backgroundColor: '#1f2937',
      borderRadius: '4px',
      overflow: 'hidden',
      position: 'relative'
    }}>
      <div style={{
        height: '100%',
        backgroundColor: '#60a5fa',
        borderRadius: '4px',
        animation: `progressBar ${duration}s linear forwards`,
        width: '0%'
      }} />
    </div>
    {message && (
      <p style={{ textAlign: 'center', marginTop: '0.5rem', fontSize: '0.875rem', color: '#9ca3af' }}>
        {message}
      </p>
    )}
    <style>{`
      @keyframes progressBar {
        from { width: 0%; }
        to { width: 100%; }
      }
    `}</style>
  </div>
);

export default ProgressBar;

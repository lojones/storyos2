import React, { useState, useRef, useEffect } from 'react';

interface PlayerInputProps {
  onSubmit: (value: string) => void;
  disabled?: boolean;
  gameSpeed: number;
  onGameSpeedChange: (speed: number) => void;
}

const PlayerInput: React.FC<PlayerInputProps> = ({ onSubmit, disabled, gameSpeed, onGameSpeedChange }) => {
  const [value, setValue] = useState('');
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!value.trim()) return;
    onSubmit(value.trim());
    setValue('');
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.key === 'Enter' || event.key === 'NumpadEnter') && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      if (!value.trim()) return;
      onSubmit(value.trim());
      setValue('');
    }
  };

  const handleSpeedSelect = (speed: number) => {
    onGameSpeedChange(speed);
    setShowSpeedMenu(false);
  };

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        menuRef.current &&
        buttonRef.current &&
        !menuRef.current.contains(event.target as Node) &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setShowSpeedMenu(false);
      }
    };

    if (showSpeedMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showSpeedMenu]);

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '1rem', marginTop: '1rem', position: 'relative' }}>
      <div style={{ position: 'relative', flex: 1, display: 'flex', alignItems: 'stretch' }}>
        <button
          ref={buttonRef}
          type="button"
          onClick={() => setShowSpeedMenu(!showSpeedMenu)}
          disabled={disabled}
          style={{
            padding: '0.5rem',
            backgroundColor: '#374151',
            border: '1px solid #4b5563',
            borderRight: 'none',
            borderRadius: '0.25rem 0 0 0.25rem',
            color: '#9ca3af',
            cursor: disabled ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minWidth: '40px',
            transition: 'background-color 0.2s',
          }}
          onMouseEnter={(e) => {
            if (!disabled) e.currentTarget.style.backgroundColor = '#4b5563';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#374151';
          }}
          title={`Game Speed: ${gameSpeed}`}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </button>
        <textarea
          rows={3}
          placeholder="What will you do next?"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          style={{
            flex: 1,
            borderRadius: '0 0.25rem 0.25rem 0',
            borderLeft: 'none',
          }}
        />
        {showSpeedMenu && (
          <div
            ref={menuRef}
            style={{
              position: 'absolute',
              bottom: '100%',
              left: 0,
              marginBottom: '0.5rem',
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '0.5rem',
              padding: '0.5rem',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
              zIndex: 1000,
              minWidth: '200px',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Story Speed
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.25rem' }}>
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((speed) => (
                <button
                  key={speed}
                  type="button"
                  onClick={() => handleSpeedSelect(speed)}
                  style={{
                    padding: '0.5rem',
                    backgroundColor: gameSpeed === speed ? '#3b82f6' : '#374151',
                    color: gameSpeed === speed ? '#ffffff' : '#e5e7eb',
                    border: '1px solid #4b5563',
                    borderRadius: '0.25rem',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: gameSpeed === speed ? 'bold' : 'normal',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    if (gameSpeed !== speed) {
                      e.currentTarget.style.backgroundColor = '#4b5563';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (gameSpeed !== speed) {
                      e.currentTarget.style.backgroundColor = '#374151';
                    }
                  }}
                >
                  {speed}
                </button>
              ))}
            </div>
            <div style={{ fontSize: '0.625rem', color: '#6b7280', marginTop: '0.5rem', textAlign: 'center' }}>
              {gameSpeed <= 3 && 'Slow progression'}
              {gameSpeed >= 4 && gameSpeed <= 7 && 'Balanced pacing'}
              {gameSpeed >= 8 && 'Fast progression'}
            </div>
          </div>
        )}
      </div>
      <button className="primary" type="submit" disabled={disabled}>
        Send
      </button>
    </form>
  );
};

export default PlayerInput;

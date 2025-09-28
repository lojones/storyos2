import React, { useState } from 'react';

interface PlayerInputProps {
  onSubmit: (value: string) => void;
  disabled?: boolean;
}

const PlayerInput: React.FC<PlayerInputProps> = ({ onSubmit, disabled }) => {
  const [value, setValue] = useState('');

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

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
      <textarea
        rows={3}
        placeholder="What will you do next?"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <button className="primary" type="submit" disabled={disabled}>
        Send
      </button>
    </form>
  );
};

export default PlayerInput;

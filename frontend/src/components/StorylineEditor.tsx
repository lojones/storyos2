import React from 'react';

interface StorylineChapter {
  chapter_number: number;
  chapter_title: string;
  chapter_goal: string;
  chapter_summary: string;
}

interface StorylineAct {
  act_number: number;
  act_title: string;
  act_goal: string;
  chapters: StorylineChapter[];
}

interface Storyline {
  archetype: string;
  storyline_summary: string;
  protagonist_name: string;
  acts: StorylineAct[];
  theme?: string;
  main_characters: Record<string, string>;
}

interface StorylineEditorProps {
  storyline: Storyline;
  onChange: (storyline: Storyline) => void;
  readOnly?: boolean;
}

const StorylineEditor: React.FC<StorylineEditorProps> = ({ storyline, onChange, readOnly = false }) => {
  const handleFieldChange = (field: keyof Storyline, value: any) => {
    onChange({ ...storyline, [field]: value });
  };

  const handleActChange = (actIndex: number, field: keyof StorylineAct, value: any) => {
    const updatedActs = [...storyline.acts];
    updatedActs[actIndex] = { ...updatedActs[actIndex], [field]: value };
    onChange({ ...storyline, acts: updatedActs });
  };

  const handleChapterChange = (actIndex: number, chapterIndex: number, field: keyof StorylineChapter, value: any) => {
    const updatedActs = [...storyline.acts];
    const updatedChapters = [...updatedActs[actIndex].chapters];
    updatedChapters[chapterIndex] = { ...updatedChapters[chapterIndex], [field]: value };
    updatedActs[actIndex] = { ...updatedActs[actIndex], chapters: updatedChapters };
    onChange({ ...storyline, acts: updatedActs });
  };

  const handleCharacterChange = (characterName: string, value: string) => {
    const updatedCharacters = { ...storyline.main_characters, [characterName]: value };
    onChange({ ...storyline, main_characters: updatedCharacters });
  };

  const handleCharacterNameChange = (oldName: string, newName: string) => {
    if (newName.trim()) {
      const updatedCharacters = { ...storyline.main_characters };
      const description = updatedCharacters[oldName];
      delete updatedCharacters[oldName];
      updatedCharacters[newName] = description;
      onChange({ ...storyline, main_characters: updatedCharacters });
    }
  };

  const handleDeleteCharacter = (characterName: string) => {
    const updatedCharacters = { ...storyline.main_characters };
    delete updatedCharacters[characterName];
    onChange({ ...storyline, main_characters: updatedCharacters });
  };

  const handleAddCharacter = () => {
    const updatedCharacters = { ...storyline.main_characters, 'New Character': '' };
    onChange({ ...storyline, main_characters: updatedCharacters });
  };

  return (
    <div>
      {/* Storyline Section */}
      <div style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#1f2937', borderRadius: '0.5rem' }}>
        <h3 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1rem', color: '#60a5fa' }}>Storyline</h3>

        {/* Archetype (read-only) */}
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
            Archetype
          </label>
          <div style={{ padding: '0.5rem', backgroundColor: '#111827', borderRadius: '0.25rem', fontSize: '0.875rem' }}>
            {storyline.archetype}
          </div>
        </div>

        {/* Summary */}
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
            Storyline Summary
          </label>
          {readOnly ? (
            <div style={{ padding: '0.5rem', backgroundColor: '#111827', borderRadius: '0.25rem', fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>
              {storyline.storyline_summary}
            </div>
          ) : (
            <textarea
              value={storyline.storyline_summary}
              onChange={(e) => handleFieldChange('storyline_summary', e.target.value)}
              rows={3}
              style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
            />
          )}
        </div>

        {/* Protagonist Name */}
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
            Protagonist Name
          </label>
          {readOnly ? (
            <div style={{ padding: '0.5rem', backgroundColor: '#111827', borderRadius: '0.25rem', fontSize: '0.875rem' }}>
              {storyline.protagonist_name}
            </div>
          ) : (
            <input
              type="text"
              value={storyline.protagonist_name}
              onChange={(e) => handleFieldChange('protagonist_name', e.target.value)}
              style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem' }}
            />
          )}
        </div>

        {/* Theme */}
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
            Theme
          </label>
          {readOnly ? (
            <div style={{ padding: '0.5rem', backgroundColor: '#111827', borderRadius: '0.25rem', fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>
              {storyline.theme || 'N/A'}
            </div>
          ) : (
            <textarea
              value={storyline.theme || ''}
              onChange={(e) => handleFieldChange('theme', e.target.value)}
              rows={2}
              style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
            />
          )}
        </div>
      </div>

      {/* Main Characters */}
      <div style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#1f2937', borderRadius: '0.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0, fontSize: '1rem', color: '#60a5fa' }}>
            Main Characters
          </h3>
          {!readOnly && (
            <button
              className="secondary"
              onClick={handleAddCharacter}
              style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}
            >
              + Add Character
            </button>
          )}
        </div>
        {Object.entries(storyline.main_characters).map(([name, description]) => (
          <div key={name} style={{ marginBottom: '0.75rem', padding: '0.75rem', backgroundColor: '#111827', borderRadius: '0.25rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.7rem', color: '#9ca3af' }}>
                  Character Name
                </label>
                {readOnly ? (
                  <div style={{ padding: '0.4rem', fontSize: '0.875rem', color: '#e5e7eb' }}>
                    {name}
                  </div>
                ) : (
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => handleCharacterNameChange(name, e.target.value)}
                    style={{ width: '100%', padding: '0.4rem', fontSize: '0.875rem' }}
                  />
                )}
              </div>
              {!readOnly && (
                <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                  <button
                    className="secondary"
                    onClick={() => handleDeleteCharacter(name)}
                    style={{
                      padding: '0.4rem 0.75rem',
                      fontSize: '0.75rem',
                      backgroundColor: '#701a75',
                      color: '#f0abfc',
                      borderRadius: '0.5rem',
                      border: '1px solid #86198f'
                    }}
                    title="Delete character"
                  >
                    ✕
                  </button>
                </div>
              )}
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.7rem', color: '#9ca3af' }}>
                Description
              </label>
              {readOnly ? (
                <div style={{ padding: '0.5rem', fontSize: '0.875rem', color: '#d1d5db', whiteSpace: 'pre-wrap' }}>
                  {description}
                </div>
              ) : (
                <textarea
                  value={description}
                  onChange={(e) => handleCharacterChange(name, e.target.value)}
                  rows={2}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                />
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Acts and Chapters */}
      <div>
        <h3 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1rem' }}>Acts and Chapters</h3>
        {storyline.acts.map((act, actIndex) => (
          <div key={act.act_number} style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#1f2937', borderRadius: '0.375rem' }}>
            <h4 style={{ marginTop: 0, marginBottom: '0.75rem', fontSize: '0.9rem', color: '#60a5fa' }}>
              Act {act.act_number}
            </h4>

            <div style={{ marginBottom: '0.75rem' }}>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.75rem' }}>
                Act Title
              </label>
              {readOnly ? (
                <div style={{ padding: '0.5rem', backgroundColor: '#111827', borderRadius: '0.25rem', fontSize: '0.875rem' }}>
                  {act.act_title}
                </div>
              ) : (
                <input
                  type="text"
                  value={act.act_title}
                  onChange={(e) => handleActChange(actIndex, 'act_title', e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem' }}
                />
              )}
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.75rem' }}>
                Act Goal
              </label>
              {readOnly ? (
                <div style={{ padding: '0.5rem', backgroundColor: '#111827', borderRadius: '0.25rem', fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>
                  {act.act_goal}
                </div>
              ) : (
                <textarea
                  value={act.act_goal}
                  onChange={(e) => handleActChange(actIndex, 'act_goal', e.target.value)}
                  rows={2}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                />
              )}
            </div>

            {/* Chapters */}
            <div>
              <h5 style={{ marginTop: 0, marginBottom: '0.5rem', fontSize: '0.85rem' }}>Chapters</h5>
              {act.chapters.map((chapter, chapterIndex) => (
                <div key={chapter.chapter_number} style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#111827', borderRadius: '0.25rem' }}>
                  <div style={{ marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.75rem', color: '#9ca3af' }}>
                    Chapter {chapter.chapter_number}
                  </div>

                  <div style={{ marginBottom: '0.5rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.7rem' }}>
                      Chapter Title
                    </label>
                    {readOnly ? (
                      <div style={{ padding: '0.4rem', fontSize: '0.8rem', color: '#e5e7eb' }}>
                        {chapter.chapter_title}
                      </div>
                    ) : (
                      <input
                        type="text"
                        value={chapter.chapter_title}
                        onChange={(e) => handleChapterChange(actIndex, chapterIndex, 'chapter_title', e.target.value)}
                        style={{ width: '100%', padding: '0.4rem', fontSize: '0.8rem' }}
                      />
                    )}
                  </div>

                  <div style={{ marginBottom: '0.5rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.7rem' }}>
                      Chapter Goal
                    </label>
                    {readOnly ? (
                      <div style={{ padding: '0.4rem', fontSize: '0.8rem', color: '#d1d5db', whiteSpace: 'pre-wrap' }}>
                        {chapter.chapter_goal}
                      </div>
                    ) : (
                      <textarea
                        value={chapter.chapter_goal}
                        onChange={(e) => handleChapterChange(actIndex, chapterIndex, 'chapter_goal', e.target.value)}
                        rows={2}
                        style={{ width: '100%', padding: '0.4rem', fontSize: '0.8rem', resize: 'vertical' }}
                      />
                    )}
                  </div>

                  <div>
                    <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.7rem' }}>
                      Chapter Summary
                    </label>
                    {readOnly ? (
                      <div style={{ padding: '0.4rem', fontSize: '0.8rem', color: '#d1d5db', whiteSpace: 'pre-wrap' }}>
                        {chapter.chapter_summary}
                      </div>
                    ) : (
                      <textarea
                        value={chapter.chapter_summary}
                        onChange={(e) => handleChapterChange(actIndex, chapterIndex, 'chapter_summary', e.target.value)}
                        rows={6}
                        style={{ width: '100%', padding: '0.4rem', fontSize: '0.8rem', resize: 'vertical' }}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StorylineEditor;

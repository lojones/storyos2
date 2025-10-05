import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import LoadingIndicator from '../components/LoadingIndicator';

interface StoryArchetype {
  name: string;
  examples: string[];
  acts: Array<{
    act_number: number;
    name: string;
    goal: string;
    chapters: Array<{
      chapter_number: number;
      goal: string;
    }>;
  }>;
}

interface StoryArchetypes {
  structure: {
    acts_per_story: number[];
    total_chapters: number;
  };
  archetypes: StoryArchetype[];
}

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
  acts: StorylineAct[];
  theme?: string;
  main_characters: Record<string, string>;
}

const StoryArchitect: React.FC = () => {
  const navigate = useNavigate();
  const [archetypes, setArchetypes] = useState<StoryArchetypes | null>(null);
  const [selectedArchetype, setSelectedArchetype] = useState<string>('');
  const [scenarioDetails, setScenarioDetails] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedStoryline, setGeneratedStoryline] = useState<Storyline | null>(null);

  useEffect(() => {
    const fetchArchetypes = async () => {
      setIsLoading(true);
      try {
        const response = await axios.get<StoryArchetypes>('/api/story-architect/archetypes');
        setArchetypes(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to load story archetypes');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchArchetypes();
  }, []);

  const handleSubmit = async () => {
    if (!selectedArchetype || !scenarioDetails.trim()) {
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await axios.post<Storyline>('/api/story-architect/generate-storyline', {
        archetype_name: selectedArchetype,
        description: scenarioDetails,
      });

      setGeneratedStoryline(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate storyline');
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFieldChange = (field: keyof Storyline, value: any) => {
    if (generatedStoryline) {
      setGeneratedStoryline({ ...generatedStoryline, [field]: value });
    }
  };

  const handleActChange = (actIndex: number, field: keyof StorylineAct, value: any) => {
    if (generatedStoryline) {
      const updatedActs = [...generatedStoryline.acts];
      updatedActs[actIndex] = { ...updatedActs[actIndex], [field]: value };
      setGeneratedStoryline({ ...generatedStoryline, acts: updatedActs });
    }
  };

  const handleChapterChange = (actIndex: number, chapterIndex: number, field: keyof StorylineChapter, value: any) => {
    if (generatedStoryline) {
      const updatedActs = [...generatedStoryline.acts];
      const updatedChapters = [...updatedActs[actIndex].chapters];
      updatedChapters[chapterIndex] = { ...updatedChapters[chapterIndex], [field]: value };
      updatedActs[actIndex] = { ...updatedActs[actIndex], chapters: updatedChapters };
      setGeneratedStoryline({ ...generatedStoryline, acts: updatedActs });
    }
  };

  const handleCharacterChange = (characterName: string, value: string) => {
    if (generatedStoryline) {
      const updatedCharacters = { ...generatedStoryline.main_characters, [characterName]: value };
      setGeneratedStoryline({ ...generatedStoryline, main_characters: updatedCharacters });
    }
  };

  const handleSave = () => {
    // TODO: Implement save logic
    console.log('Saving storyline:', generatedStoryline);
  };

  const selectedArchetypeDetails = archetypes?.archetypes.find(
    (arch) => arch.name === selectedArchetype
  );

  if (isLoading) {
    return (
      <div className="main-content">
        <div className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <LoadingIndicator message="Loading story archetypes..." />
        </div>
      </div>
    );
  }

  if (isGenerating) {
    return (
      <div className="main-content">
        <div className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <LoadingIndicator message="Generating storyline with AI..." />
        </div>
      </div>
    );
  }

  return (
    <div className="main-content">
      <div className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h1 style={{ margin: 0 }}>Story Architect</h1>
            <p style={{ margin: '0.25rem 0 0 0', color: '#9ca3af' }}>
              Design your story using proven narrative structures
            </p>
          </div>
          <button
            className="primary"
            onClick={() => navigate('/scenarios')}
          >
            Back to Scenario Repository
          </button>
        </div>

        {error && (
          <div style={{ color: '#f87171', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {!generatedStoryline ? (
          <div className="card" style={{ marginTop: '1.5rem' }}>
            <h2 style={{ marginTop: 0 }}>Select Story Archetype</h2>

            <div style={{ marginBottom: '1.5rem' }}>
              <label htmlFor="archetype-select" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                Archetype
              </label>
              <select
                id="archetype-select"
                className="scenario-input"
                value={selectedArchetype}
                onChange={(e) => setSelectedArchetype(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', fontSize: '1rem' }}
              >
                <option value="">-- Select an archetype --</option>
                {archetypes?.archetypes.map((archetype) => (
                  <option key={archetype.name} value={archetype.name}>
                    {archetype.name}
                  </option>
                ))}
              </select>
            </div>

            {selectedArchetypeDetails && (
              <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#1f2937', borderRadius: '0.375rem' }}>
                <h3 style={{ marginTop: 0, fontSize: '1rem', color: '#60a5fa' }}>
                  {selectedArchetypeDetails.name}
                </h3>
                <p style={{ margin: '0.5rem 0', fontSize: '0.875rem', color: '#9ca3af' }}>
                  <strong>Examples:</strong> {selectedArchetypeDetails.examples.join(', ')}
                </p>
                <div style={{ marginTop: '1rem' }}>
                  <strong style={{ fontSize: '0.875rem' }}>Structure:</strong>
                  <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem', fontSize: '0.875rem', color: '#d1d5db' }}>
                    {selectedArchetypeDetails.acts.map((act) => (
                      <li key={act.act_number} style={{ marginBottom: '0.5rem' }}>
                        <strong>Act {act.act_number}: {act.name}</strong> - {act.goal}
                        <span style={{ color: '#9ca3af', marginLeft: '0.5rem' }}>
                          ({act.chapters.length} chapters)
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            <div style={{ marginBottom: '1.5rem' }}>
              <label htmlFor="scenario-details" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                Scenario Details and Storyline
              </label>
              <textarea
                id="scenario-details"
                className="scenario-textarea"
                value={scenarioDetails}
                onChange={(e) => setScenarioDetails(e.target.value)}
                placeholder="Enter scenario details and storyline details, the more details the better. But if it isn't detailed then I will enhance it so don't worry."
                rows={12}
                style={{ width: '100%', padding: '0.75rem', fontSize: '1rem', resize: 'vertical' }}
              />
            </div>

            <button
              className="primary"
              onClick={handleSubmit}
              disabled={!selectedArchetype || !scenarioDetails.trim()}
              style={{ width: '100%', padding: '0.75rem', fontSize: '1rem' }}
            >
              Generate Storyline
            </button>
          </div>
        ) : (
          <div className="card" style={{ marginTop: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0 }}>Generated Storyline</h2>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  className="secondary"
                  onClick={() => setGeneratedStoryline(null)}
                >
                  Start Over
                </button>
                <button
                  className="primary"
                  onClick={handleSave}
                >
                  Save Storyline
                </button>
              </div>
            </div>

            {/* Archetype (read-only) */}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                Archetype
              </label>
              <div style={{ padding: '0.5rem', backgroundColor: '#1f2937', borderRadius: '0.25rem', fontSize: '0.875rem' }}>
                {generatedStoryline.archetype}
              </div>
            </div>

            {/* Summary */}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                Storyline Summary
              </label>
              <textarea
                value={generatedStoryline.storyline_summary}
                onChange={(e) => handleFieldChange('storyline_summary', e.target.value)}
                rows={3}
                style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
              />
            </div>

            {/* Theme */}
            {generatedStoryline.theme && (
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Theme
                </label>
                <textarea
                  value={generatedStoryline.theme}
                  onChange={(e) => handleFieldChange('theme', e.target.value)}
                  rows={2}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                />
              </div>
            )}

            {/* Main Characters */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.875rem' }}>
                Main Characters
              </label>
              {Object.entries(generatedStoryline.main_characters).map(([name, description]) => (
                <div key={name} style={{ marginBottom: '0.75rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.75rem', color: '#9ca3af' }}>
                    {name}
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => handleCharacterChange(name, e.target.value)}
                    rows={2}
                    style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                  />
                </div>
              ))}
            </div>

            {/* Acts and Chapters */}
            <div>
              <h3 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1rem' }}>Acts and Chapters</h3>
              {generatedStoryline.acts.map((act, actIndex) => (
                <div key={act.act_number} style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#1f2937', borderRadius: '0.375rem' }}>
                  <h4 style={{ marginTop: 0, marginBottom: '0.75rem', fontSize: '0.9rem', color: '#60a5fa' }}>
                    Act {act.act_number}
                  </h4>

                  <div style={{ marginBottom: '0.75rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.75rem' }}>
                      Act Title
                    </label>
                    <input
                      type="text"
                      value={act.act_title}
                      onChange={(e) => handleActChange(actIndex, 'act_title', e.target.value)}
                      style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem' }}
                    />
                  </div>

                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.75rem' }}>
                      Act Goal
                    </label>
                    <textarea
                      value={act.act_goal}
                      onChange={(e) => handleActChange(actIndex, 'act_goal', e.target.value)}
                      rows={2}
                      style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                    />
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
                          <input
                            type="text"
                            value={chapter.chapter_title}
                            onChange={(e) => handleChapterChange(actIndex, chapterIndex, 'chapter_title', e.target.value)}
                            style={{ width: '100%', padding: '0.4rem', fontSize: '0.8rem' }}
                          />
                        </div>

                        <div style={{ marginBottom: '0.5rem' }}>
                          <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.7rem' }}>
                            Chapter Goal
                          </label>
                          <textarea
                            value={chapter.chapter_goal}
                            onChange={(e) => handleChapterChange(actIndex, chapterIndex, 'chapter_goal', e.target.value)}
                            rows={2}
                            style={{ width: '100%', padding: '0.4rem', fontSize: '0.8rem', resize: 'vertical' }}
                          />
                        </div>

                        <div>
                          <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.7rem' }}>
                            Chapter Summary
                          </label>
                          <textarea
                            value={chapter.chapter_summary}
                            onChange={(e) => handleChapterChange(actIndex, chapterIndex, 'chapter_summary', e.target.value)}
                            rows={6}
                            style={{ width: '100%', padding: '0.4rem', fontSize: '0.8rem', resize: 'vertical' }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StoryArchitect;

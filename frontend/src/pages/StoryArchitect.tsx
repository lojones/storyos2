import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LoadingIndicator from '../components/LoadingIndicator';
import { useAuth } from '../hooks/useAuth';
import { apiClient } from '../api/client';

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
  protagonist_name: string;
  acts: StorylineAct[];
  theme?: string;
  main_characters: Record<string, string>;
}

interface ScenarioForm {
  scenario_id: string;
  name: string;
  description: string;
  setting: string;
  dungeon_master_behaviour: string;
  player_name: string;
  role: string;
  initial_location: string;
  visibility: 'public' | 'private';
  storyline: Storyline;
}

const StoryArchitect: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [archetypes, setArchetypes] = useState<StoryArchetypes | null>(null);
  const [selectedArchetype, setSelectedArchetype] = useState<string>('');
  const [scenarioDetails, setScenarioDetails] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [scenarioForm, setScenarioForm] = useState<ScenarioForm | null>(null);

  useEffect(() => {
    const fetchArchetypes = async () => {
      setIsLoading(true);
      try {
        const response = await apiClient.get<StoryArchetypes>('/story-architect/archetypes');
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
      const response = await apiClient.post<Storyline>('/story-architect/generate-storyline', {
        archetype_name: selectedArchetype,
        description: scenarioDetails,
      });

      const storyline = response.data;

      // Create a scenario form with the generated storyline
      const defaultDMBehaviour = `As DM, you **vividly narrate the unfolding world** and **role-play every NPC** with clear personalities, motives, and emotions. Your goal is to **keep the story moving forward dynamically**, maintaining momentum and immersion in every exchange.

* **Always describe scenes with sensory detail** — what the player sees, hears, feels, and senses — giving each setting a distinct atmosphere.
* **React immediately to the player's choices**: assume their actions succeed or fail naturally based on context, and describe the world's response and evolving consequences.
* **Never rephrase, confirm, or repeat** what the player does — begin your narration *after* their action has occurred, showing impact and ripple effects.
* **End every turn with a clear prompt**, such as *"What do you do?"*, to reinforce player agency and keep the story interactive.
* **Keep tension alive**: raise stakes, reveal surprises, and let consequences accumulate over time.
* **NPCs should feel real** — each with distinct motivations, flaws, and goals that can help or hinder the player's journey.
* **Adapt tone and pacing** to the archetype and genre — mystery should feel tense and deliberate; adventure should feel expansive and propulsive; tragedy should feel inevitable and heavy.
* **Track continuity carefully** — characters' states, locations, time of day, and unresolved story threads — ensuring logical, consistent cause and effect.
* **Avoid speaking as the player** or narrating their inner thoughts; instead, respond to what they *say or do*, keeping their agency absolute.
* **If the player gives only dialogue**, respond *only* with NPC dialogue — no narration.
* **If the player provides an action, decision, or thought**, narrate the outcome and next state of the world.
* **Reward curiosity, creativity, and risk**, but allow natural setbacks and moral consequences to make the world feel responsive and alive.

Your tone should always balance **momentum, immersion, and emotional stakes** — every scene should feel like the story is evolving meaningfully, one decision at a time.`;

      const newScenarioForm: ScenarioForm = {
        scenario_id: '',
        name: '',
        description: scenarioDetails,
        setting: storyline.storyline_summary,
        dungeon_master_behaviour: defaultDMBehaviour,
        player_name: storyline.protagonist_name || '',
        role: '',
        initial_location: '',
        visibility: 'private',
        storyline: {
          ...storyline,
          protagonist_name: storyline.protagonist_name || ''
        },
      };

      setScenarioForm(newScenarioForm);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate storyline');
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleScenarioFieldChange = (field: keyof ScenarioForm, value: any) => {
    if (scenarioForm) {
      setScenarioForm({ ...scenarioForm, [field]: value });
    }
  };

  const handleStorylineFieldChange = (field: keyof Storyline, value: any) => {
    if (scenarioForm) {
      setScenarioForm({ ...scenarioForm, storyline: { ...scenarioForm.storyline, [field]: value } });
    }
  };

  const handleActChange = (actIndex: number, field: keyof StorylineAct, value: any) => {
    if (scenarioForm) {
      const updatedActs = [...scenarioForm.storyline.acts];
      updatedActs[actIndex] = { ...updatedActs[actIndex], [field]: value };
      setScenarioForm({
        ...scenarioForm,
        storyline: { ...scenarioForm.storyline, acts: updatedActs }
      });
    }
  };

  const handleChapterChange = (actIndex: number, chapterIndex: number, field: keyof StorylineChapter, value: any) => {
    if (scenarioForm) {
      const updatedActs = [...scenarioForm.storyline.acts];
      const updatedChapters = [...updatedActs[actIndex].chapters];
      updatedChapters[chapterIndex] = { ...updatedChapters[chapterIndex], [field]: value };
      updatedActs[actIndex] = { ...updatedActs[actIndex], chapters: updatedChapters };
      setScenarioForm({
        ...scenarioForm,
        storyline: { ...scenarioForm.storyline, acts: updatedActs }
      });
    }
  };

  const handleCharacterChange = (characterName: string, value: string) => {
    if (scenarioForm) {
      const updatedCharacters = { ...scenarioForm.storyline.main_characters, [characterName]: value };
      setScenarioForm({
        ...scenarioForm,
        storyline: { ...scenarioForm.storyline, main_characters: updatedCharacters }
      });
    }
  };

  const handleCharacterNameChange = (oldName: string, newName: string) => {
    if (scenarioForm && newName.trim()) {
      const updatedCharacters = { ...scenarioForm.storyline.main_characters };
      const description = updatedCharacters[oldName];
      delete updatedCharacters[oldName];
      updatedCharacters[newName] = description;
      setScenarioForm({
        ...scenarioForm,
        storyline: { ...scenarioForm.storyline, main_characters: updatedCharacters }
      });
    }
  };

  const handleDeleteCharacter = (characterName: string) => {
    if (scenarioForm) {
      const updatedCharacters = { ...scenarioForm.storyline.main_characters };
      delete updatedCharacters[characterName];
      setScenarioForm({
        ...scenarioForm,
        storyline: { ...scenarioForm.storyline, main_characters: updatedCharacters }
      });
    }
  };

  const handleAddCharacter = () => {
    if (scenarioForm) {
      const updatedCharacters = { ...scenarioForm.storyline.main_characters, 'New Character': '' };
      setScenarioForm({
        ...scenarioForm,
        storyline: { ...scenarioForm.storyline, main_characters: updatedCharacters }
      });
    }
  };

  const handleSave = async () => {
    if (!scenarioForm) return;

    // Validate required fields
    if (!scenarioForm.scenario_id.trim()) {
      setError('Scenario ID is required');
      return;
    }
    if (!scenarioForm.name.trim()) {
      setError('Scenario Name is required');
      return;
    }

    try {
      setError(null);

      // Call the create scenario API
      await apiClient.post('/scenarios/', {
        ...scenarioForm,
        author: user?.userId || 'unknown',
        version: 1,
        created_at: new Date().toISOString(),
      });

      // Navigate back to scenarios page
      navigate('/scenarios');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save scenario');
      console.error('Error saving scenario:', err);
    }
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

        {!scenarioForm ? (
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
              <h2 style={{ margin: 0 }}>Edit Scenario</h2>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  className="secondary"
                  onClick={() => setScenarioForm(null)}
                >
                  Start Over
                </button>
                <button
                  className="primary"
                  onClick={handleSave}
                >
                  Save Scenario
                </button>
              </div>
            </div>

            {/* Basic Scenario Fields */}
            <div style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#1f2937', borderRadius: '0.5rem' }}>
              <h3 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1rem', color: '#60a5fa' }}>Basic Information</h3>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Scenario ID *
                </label>
                <input
                  type="text"
                  value={scenarioForm.scenario_id}
                  onChange={(e) => handleScenarioFieldChange('scenario_id', e.target.value)}
                  placeholder="unique-scenario-id"
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Scenario Name *
                </label>
                <input
                  type="text"
                  value={scenarioForm.name}
                  onChange={(e) => handleScenarioFieldChange('name', e.target.value)}
                  placeholder="Display name for the scenario"
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Description *
                </label>
                <textarea
                  value={scenarioForm.description}
                  onChange={(e) => handleScenarioFieldChange('description', e.target.value)}
                  placeholder="Full description of the scenario and player role"
                  rows={3}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Visibility
                </label>
                <select
                  value={scenarioForm.visibility}
                  onChange={(e) => handleScenarioFieldChange('visibility', e.target.value as 'public' | 'private')}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem' }}
                >
                  <option value="private">Private</option>
                  <option value="public">Public</option>
                </select>
              </div>
            </div>

            {/* Player Information */}
            <div style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#1f2937', borderRadius: '0.5rem' }}>
              <h3 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1rem', color: '#60a5fa' }}>Player Character</h3>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Player Name *
                </label>
                <input
                  type="text"
                  value={scenarioForm.player_name}
                  onChange={(e) => handleScenarioFieldChange('player_name', e.target.value)}
                  placeholder="Name of the player character"
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Role *
                </label>
                <textarea
                  value={scenarioForm.role}
                  onChange={(e) => handleScenarioFieldChange('role', e.target.value)}
                  placeholder="Description of the player character's role and abilities"
                  rows={3}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Initial Location *
                </label>
                <textarea
                  value={scenarioForm.initial_location}
                  onChange={(e) => handleScenarioFieldChange('initial_location', e.target.value)}
                  placeholder="Starting location and initial scenario text"
                  rows={3}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                />
              </div>
            </div>

            {/* Dungeon Master Settings */}
            <div style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#1f2937', borderRadius: '0.5rem' }}>
              <h3 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1rem', color: '#60a5fa' }}>Dungeon Master</h3>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Setting *
                </label>
                <textarea
                  value={scenarioForm.setting}
                  onChange={(e) => handleScenarioFieldChange('setting', e.target.value)}
                  placeholder="Dungeon master setting and world context"
                  rows={4}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Behaviour *
                </label>
                <textarea
                  value={scenarioForm.dungeon_master_behaviour}
                  onChange={(e) => handleScenarioFieldChange('dungeon_master_behaviour', e.target.value)}
                  placeholder="Instructions for DM behavior and storytelling style"
                  rows={6}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                />
              </div>
            </div>

            {/* Storyline Section */}
            <div style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#1f2937', borderRadius: '0.5rem' }}>
              <h3 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1rem', color: '#60a5fa' }}>Storyline</h3>

              {/* Archetype (read-only) */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Archetype
                </label>
                <div style={{ padding: '0.5rem', backgroundColor: '#111827', borderRadius: '0.25rem', fontSize: '0.875rem' }}>
                  {scenarioForm.storyline.archetype}
                </div>
              </div>

              {/* Summary */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Storyline Summary
                </label>
                <textarea
                  value={scenarioForm.storyline.storyline_summary}
                  onChange={(e) => handleStorylineFieldChange('storyline_summary', e.target.value)}
                  rows={3}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                />
              </div>

              {/* Protagonist Name */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Protagonist Name
                </label>
                <input
                  type="text"
                  value={scenarioForm.storyline.protagonist_name}
                  onChange={(e) => handleStorylineFieldChange('protagonist_name', e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem' }}
                />
              </div>

              {/* Theme */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.875rem' }}>
                  Theme
                </label>
                <textarea
                  value={scenarioForm.storyline.theme || ''}
                  onChange={(e) => handleStorylineFieldChange('theme', e.target.value)}
                  rows={2}
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                />
              </div>
            </div>

            {/* Main Characters */}
            <div style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#1f2937', borderRadius: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0, fontSize: '1rem', color: '#60a5fa' }}>
                  Main Characters
                </h3>
                <button
                  className="secondary"
                  onClick={handleAddCharacter}
                  style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}
                >
                  + Add Character
                </button>
              </div>
              {Object.entries(scenarioForm.storyline.main_characters).map(([name, description]) => (
                <div key={name} style={{ marginBottom: '0.75rem', padding: '0.75rem', backgroundColor: '#111827', borderRadius: '0.25rem' }}>
                  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.7rem', color: '#9ca3af' }}>
                        Character Name
                      </label>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => handleCharacterNameChange(name, e.target.value)}
                        style={{ width: '100%', padding: '0.4rem', fontSize: '0.875rem' }}
                      />
                    </div>
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
                  </div>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.7rem', color: '#9ca3af' }}>
                      Description
                    </label>
                    <textarea
                      value={description}
                      onChange={(e) => handleCharacterChange(name, e.target.value)}
                      rows={2}
                      style={{ width: '100%', padding: '0.5rem', fontSize: '0.875rem', resize: 'vertical' }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Acts and Chapters */}
            <div>
              <h3 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1rem' }}>Acts and Chapters</h3>
              {scenarioForm.storyline.acts.map((act, actIndex) => (
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

import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { scenarioAPI } from '../api/client';

interface Scenario {
  scenario_id: string;
  name?: string;
  description?: string;
  [key: string]: any;
}

const Scenarios: React.FC = () => {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editedFields, setEditedFields] = useState<Record<string, any>>({});

  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        const response = await scenarioAPI.list();
        const items = response.data ?? [];
        setScenarios(items);
        if (items.length > 0) {
          setSelectedScenario(items[0]);
        }
      } catch (err) {
        setError('Failed to load scenarios');
        console.error(err);
      }
    };

    fetchScenarios();
  }, []);

  const handleSelect = async (scenarioId: string) => {
    try {
      const response = await scenarioAPI.get(scenarioId);
      setSelectedScenario(response.data);
      setEditMode(false);
      setEditedFields({});
      setError(null);
    } catch (err) {
      setError('Failed to load scenario details');
      console.error(err);
    }
  };

  const handleFieldEdit = (fieldName: string, value: any) => {
    setEditedFields(prev => ({ ...prev, [fieldName]: value }));
  };

  const handleSave = async () => {
    if (!selectedScenario) return;

    try {
      // Increment version number if numeric
      let newVersion = editedFields.version;
      if (newVersion === undefined && selectedScenario.version !== undefined) {
        const currentVersion = selectedScenario.version;
        if (typeof currentVersion === 'number') {
          newVersion = currentVersion + 1;
        } else if (typeof currentVersion === 'string') {
          const parsed = parseFloat(currentVersion);
          if (!isNaN(parsed)) {
            newVersion = Math.floor(parsed) + 1;
          }
        }
      }

      const updateData = { ...editedFields };
      if (newVersion !== undefined) {
        updateData.version = newVersion;
      }

      await scenarioAPI.update(selectedScenario.scenario_id, updateData);

      // Refresh the scenario
      const response = await scenarioAPI.get(selectedScenario.scenario_id);
      setSelectedScenario(response.data);

      // Update in the list
      setScenarios(prev =>
        prev.map(s =>
          s.scenario_id === selectedScenario.scenario_id ? response.data : s
        )
      );

      setEditMode(false);
      setEditedFields({});
      setError(null);
    } catch (err) {
      setError('Failed to save scenario');
      console.error(err);
    }
  };

  const handleDiscard = () => {
    setEditMode(false);
    setEditedFields({});
    setError(null);
  };

  const getFieldValue = (fieldName: string) => {
    if (editedFields.hasOwnProperty(fieldName)) {
      return editedFields[fieldName];
    }
    return selectedScenario?.[fieldName] ?? '';
  };

  return (
    <div className="main-content" style={{ maxWidth: '980px', margin: '0 auto' }}>
      <div className="panel">
        <h1>Scenario Repository</h1>
        <p style={{ opacity: 0.7 }}>Inspect available mission frameworks and their metadata.</p>
        {error && <div style={{ color: '#f87171' }}>{error}</div>}
        <div style={{ display: 'flex', gap: '1.5rem', marginTop: '2rem', alignItems: 'flex-start' }}>
          <div style={{ flex: '0 0 260px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {scenarios.map((scenario) => (
              <button
                key={scenario.scenario_id}
                className="primary"
                style={{
                  background:
                    selectedScenario?.scenario_id === scenario.scenario_id
                      ? 'linear-gradient(135deg, #8b5cf6, #6366f1)'
                      : 'rgba(148, 163, 184, 0.16)'
                }}
                onClick={() => handleSelect(scenario.scenario_id)}
              >
                {scenario.name ?? scenario.scenario_id}
              </button>
            ))}
          </div>
          <div className="card" style={{ flex: '1 1 auto', minHeight: '260px' }}>
            {selectedScenario ? (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h2>{selectedScenario.name ?? selectedScenario.scenario_id}</h2>
                  {editMode ? (
                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                      <button
                        className="primary"
                        onClick={handleSave}
                        style={{ padding: '0.5rem 1rem', background: 'linear-gradient(135deg, #10b981, #059669)' }}
                      >
                        Save
                      </button>
                      <button
                        className="primary"
                        onClick={handleDiscard}
                        style={{ padding: '0.5rem 1rem', background: 'rgba(148, 163, 184, 0.16)' }}
                      >
                        Discard
                      </button>
                    </div>
                  ) : (
                    <button
                      className="primary"
                      onClick={() => setEditMode(true)}
                      style={{ padding: '0.5rem 1rem' }}
                    >
                      Edit
                    </button>
                  )}
                </div>

                <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  {/* Scenario ID */}
                  <div>
                    <strong style={{ display: 'block', marginBottom: '0.5rem', color: '#a78bfa' }}>Scenario ID</strong>
                    <div style={{ opacity: 0.8 }}>{selectedScenario.scenario_id}</div>
                  </div>

                  {/* Description (editable) */}
                  <div>
                    <strong style={{ display: 'block', marginBottom: '0.5rem', color: '#a78bfa' }}>Description</strong>
                    {editMode ? (
                      <textarea
                        value={getFieldValue('description')}
                        onChange={(e) => handleFieldEdit('description', e.target.value)}
                        style={{
                          width: '100%',
                          minHeight: '120px',
                          background: 'rgba(15, 23, 42, 0.5)',
                          border: '1px solid rgba(139, 92, 246, 0.3)',
                          borderRadius: '0.5rem',
                          padding: '1rem',
                          color: 'inherit',
                          fontFamily: 'inherit',
                          fontSize: 'inherit',
                          lineHeight: '1.6',
                          resize: 'vertical'
                        }}
                      />
                    ) : (
                      <div style={{
                        opacity: 0.8,
                        background: 'rgba(15, 23, 42, 0.3)',
                        padding: '1rem',
                        borderRadius: '0.5rem',
                        lineHeight: '1.6'
                      }}>
                        <ReactMarkdown>{selectedScenario.description ?? ''}</ReactMarkdown>
                      </div>
                    )}
                  </div>

                  {/* Setting (editable) */}
                  {(selectedScenario.setting || editMode) && (
                    <div>
                      <strong style={{ display: 'block', marginBottom: '0.5rem', color: '#a78bfa' }}>Setting</strong>
                      {editMode ? (
                        <textarea
                          value={getFieldValue('setting')}
                          onChange={(e) => handleFieldEdit('setting', e.target.value)}
                          style={{
                            width: '100%',
                            minHeight: '120px',
                            background: 'rgba(15, 23, 42, 0.5)',
                            border: '1px solid rgba(139, 92, 246, 0.3)',
                            borderRadius: '0.5rem',
                            padding: '1rem',
                            color: 'inherit',
                            fontFamily: 'inherit',
                            fontSize: 'inherit',
                            lineHeight: '1.6',
                            resize: 'vertical'
                          }}
                        />
                      ) : (
                        <div style={{
                          opacity: 0.8,
                          background: 'rgba(15, 23, 42, 0.3)',
                          padding: '1rem',
                          borderRadius: '0.5rem',
                          lineHeight: '1.6'
                        }}>
                          <ReactMarkdown>{selectedScenario.setting ?? ''}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Dungeon Master Behaviour (editable) */}
                  {(selectedScenario.dungeon_master_behaviour || editMode) && (
                    <div>
                      <strong style={{ display: 'block', marginBottom: '0.5rem', color: '#a78bfa' }}>Dungeon Master Behaviour</strong>
                      {editMode ? (
                        <textarea
                          value={getFieldValue('dungeon_master_behaviour')}
                          onChange={(e) => handleFieldEdit('dungeon_master_behaviour', e.target.value)}
                          style={{
                            width: '100%',
                            minHeight: '120px',
                            background: 'rgba(15, 23, 42, 0.5)',
                            border: '1px solid rgba(139, 92, 246, 0.3)',
                            borderRadius: '0.5rem',
                            padding: '1rem',
                            color: 'inherit',
                            fontFamily: 'inherit',
                            fontSize: 'inherit',
                            lineHeight: '1.6',
                            resize: 'vertical'
                          }}
                        />
                      ) : (
                        <div style={{
                          opacity: 0.8,
                          background: 'rgba(15, 23, 42, 0.3)',
                          padding: '1rem',
                          borderRadius: '0.5rem',
                          lineHeight: '1.6'
                        }}>
                          <ReactMarkdown>{selectedScenario.dungeon_master_behaviour ?? ''}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Player Name (editable) */}
                  {(selectedScenario.player_name || editMode) && (
                    <div>
                      <strong style={{ display: 'block', marginBottom: '0.5rem', color: '#a78bfa' }}>Player Name</strong>
                      {editMode ? (
                        <input
                          type="text"
                          value={getFieldValue('player_name')}
                          onChange={(e) => handleFieldEdit('player_name', e.target.value)}
                          style={{
                            width: '100%',
                            background: 'rgba(15, 23, 42, 0.5)',
                            border: '1px solid rgba(139, 92, 246, 0.3)',
                            borderRadius: '0.5rem',
                            padding: '0.75rem',
                            color: 'inherit',
                            fontFamily: 'inherit',
                            fontSize: 'inherit'
                          }}
                        />
                      ) : (
                        <div style={{
                          opacity: 0.8,
                          background: 'rgba(15, 23, 42, 0.3)',
                          padding: '1rem',
                          borderRadius: '0.5rem'
                        }}>
                          {selectedScenario.player_name}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Role (editable) */}
                  {(selectedScenario.role || editMode) && (
                    <div>
                      <strong style={{ display: 'block', marginBottom: '0.5rem', color: '#a78bfa' }}>Role</strong>
                      {editMode ? (
                        <input
                          type="text"
                          value={getFieldValue('role')}
                          onChange={(e) => handleFieldEdit('role', e.target.value)}
                          style={{
                            width: '100%',
                            background: 'rgba(15, 23, 42, 0.5)',
                            border: '1px solid rgba(139, 92, 246, 0.3)',
                            borderRadius: '0.5rem',
                            padding: '0.75rem',
                            color: 'inherit',
                            fontFamily: 'inherit',
                            fontSize: 'inherit'
                          }}
                        />
                      ) : (
                        <div style={{
                          opacity: 0.8,
                          background: 'rgba(15, 23, 42, 0.3)',
                          padding: '1rem',
                          borderRadius: '0.5rem'
                        }}>
                          {selectedScenario.role}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Initial Location (editable) */}
                  {(selectedScenario.initial_location || editMode) && (
                    <div>
                      <strong style={{ display: 'block', marginBottom: '0.5rem', color: '#a78bfa' }}>Initial Location</strong>
                      {editMode ? (
                        <input
                          type="text"
                          value={getFieldValue('initial_location')}
                          onChange={(e) => handleFieldEdit('initial_location', e.target.value)}
                          style={{
                            width: '100%',
                            background: 'rgba(15, 23, 42, 0.5)',
                            border: '1px solid rgba(139, 92, 246, 0.3)',
                            borderRadius: '0.5rem',
                            padding: '0.75rem',
                            color: 'inherit',
                            fontFamily: 'inherit',
                            fontSize: 'inherit'
                          }}
                        />
                      ) : (
                        <div style={{
                          opacity: 0.8,
                          background: 'rgba(15, 23, 42, 0.3)',
                          padding: '1rem',
                          borderRadius: '0.5rem'
                        }}>
                          {selectedScenario.initial_location}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Other non-editable fields */}
                  {Object.entries(selectedScenario)
                    .filter(([key]) => !['scenario_id', 'name', 'description', 'setting', 'dungeon_master_behaviour', 'player_name', 'role', 'initial_location'].includes(key))
                    .map(([key, value]) => (
                      <div key={key}>
                        <strong style={{ display: 'block', marginBottom: '0.5rem', color: '#a78bfa' }}>
                          {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                        </strong>
                        <div style={{
                          opacity: 0.8,
                          background: 'rgba(15, 23, 42, 0.3)',
                          padding: '1rem',
                          borderRadius: '0.5rem'
                        }}>
                          {typeof value === 'object' ? (
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                              {JSON.stringify(value, null, 2)}
                            </pre>
                          ) : (
                            String(value)
                          )}
                        </div>
                      </div>
                    ))
                  }
                </div>
              </>
            ) : (
              <p>No scenario selected.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Scenarios;

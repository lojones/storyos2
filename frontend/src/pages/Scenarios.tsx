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
    <div className="main-content scenarios-container">
      <div className="panel">
        <h1>Scenario Repository</h1>
        <p className="scenarios-description">Inspect available mission frameworks and their metadata.</p>
        {error && <div style={{ color: '#f87171' }}>{error}</div>}
        <div className="scenarios-layout">
          <div className="scenarios-sidebar">
            {scenarios.map((scenario) => (
              <button
                key={scenario.scenario_id}
                className={`primary scenario-list-button ${
                  selectedScenario?.scenario_id === scenario.scenario_id ? 'selected' : ''
                }`}
                onClick={() => handleSelect(scenario.scenario_id)}
              >
                {scenario.name ?? scenario.scenario_id}
              </button>
            ))}
          </div>
          <div className="card scenarios-detail">
            {selectedScenario ? (
              <>
                <div className="scenario-header">
                  <h2>{selectedScenario.name ?? selectedScenario.scenario_id}</h2>
                  {editMode ? (
                    <div className="scenario-actions">
                      <button className="primary scenario-save-button" onClick={handleSave}>
                        Save
                      </button>
                      <button className="primary scenario-discard-button" onClick={handleDiscard}>
                        Discard
                      </button>
                    </div>
                  ) : (
                    <button className="primary scenario-edit-button" onClick={() => setEditMode(true)}>
                      Edit
                    </button>
                  )}
                </div>

                <div className="scenario-fields">
                  {/* Scenario ID */}
                  <div>
                    <strong className="scenario-field-label">Scenario ID</strong>
                    <div className="scenario-field-value">{selectedScenario.scenario_id}</div>
                  </div>

                  {/* Description (editable) */}
                  <div>
                    <strong className="scenario-field-label">Description</strong>
                    {editMode ? (
                      <textarea
                        className="scenario-textarea"
                        value={getFieldValue('description')}
                        onChange={(e) => handleFieldEdit('description', e.target.value)}
                      />
                    ) : (
                      <div className="scenario-field-content">
                        <ReactMarkdown>{selectedScenario.description ?? ''}</ReactMarkdown>
                      </div>
                    )}
                  </div>

                  {/* Setting (editable) */}
                  {(selectedScenario.setting || editMode) && (
                    <div>
                      <strong className="scenario-field-label">Setting</strong>
                      {editMode ? (
                        <textarea
                          className="scenario-textarea"
                          value={getFieldValue('setting')}
                          onChange={(e) => handleFieldEdit('setting', e.target.value)}
                        />
                      ) : (
                        <div className="scenario-field-content">
                          <ReactMarkdown>{selectedScenario.setting ?? ''}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Dungeon Master Behaviour (editable) */}
                  {(selectedScenario.dungeon_master_behaviour || editMode) && (
                    <div>
                      <strong className="scenario-field-label">Dungeon Master Behaviour</strong>
                      {editMode ? (
                        <textarea
                          className="scenario-textarea"
                          value={getFieldValue('dungeon_master_behaviour')}
                          onChange={(e) => handleFieldEdit('dungeon_master_behaviour', e.target.value)}
                        />
                      ) : (
                        <div className="scenario-field-content">
                          <ReactMarkdown>{selectedScenario.dungeon_master_behaviour ?? ''}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Player Name (editable) */}
                  {(selectedScenario.player_name || editMode) && (
                    <div>
                      <strong className="scenario-field-label">Player Name</strong>
                      {editMode ? (
                        <input
                          type="text"
                          className="scenario-input"
                          value={getFieldValue('player_name')}
                          onChange={(e) => handleFieldEdit('player_name', e.target.value)}
                        />
                      ) : (
                        <div className="scenario-field-content">
                          {selectedScenario.player_name}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Role (editable) */}
                  {(selectedScenario.role || editMode) && (
                    <div>
                      <strong className="scenario-field-label">Role</strong>
                      {editMode ? (
                        <input
                          type="text"
                          className="scenario-input"
                          value={getFieldValue('role')}
                          onChange={(e) => handleFieldEdit('role', e.target.value)}
                        />
                      ) : (
                        <div className="scenario-field-content">
                          {selectedScenario.role}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Initial Location (editable) */}
                  {(selectedScenario.initial_location || editMode) && (
                    <div>
                      <strong className="scenario-field-label">Initial Location</strong>
                      {editMode ? (
                        <input
                          type="text"
                          className="scenario-input"
                          value={getFieldValue('initial_location')}
                          onChange={(e) => handleFieldEdit('initial_location', e.target.value)}
                        />
                      ) : (
                        <div className="scenario-field-content">
                          {selectedScenario.initial_location}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Visibility (editable) */}
                  {(selectedScenario.visibility || editMode) && (
                    <div>
                      <strong className="scenario-field-label">Visibility</strong>
                      {editMode ? (
                        <select
                          className="scenario-input"
                          value={getFieldValue('visibility') || 'public'}
                          onChange={(e) => handleFieldEdit('visibility', e.target.value)}
                        >
                          <option value="public">public</option>
                          <option value="private">private</option>
                        </select>
                      ) : (
                        <div className="scenario-field-content">
                          {selectedScenario.visibility}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Other non-editable fields */}
                  {Object.entries(selectedScenario)
                    .filter(([key]) => !['scenario_id', 'name', 'description', 'setting', 'dungeon_master_behaviour', 'player_name', 'role', 'initial_location', 'visibility'].includes(key))
                    .map(([key, value]) => (
                      <div key={key}>
                        <strong className="scenario-field-label">
                          {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                        </strong>
                        <div className="scenario-field-content">
                          {typeof value === 'object' ? (
                            <pre className="scenario-json-display">
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

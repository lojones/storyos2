import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { useSelector } from 'react-redux';
import { scenarioAPI } from '../api/client';
import LoadingIndicator from '../components/LoadingIndicator';
import type { RootState } from '../store';

interface Scenario {
  scenario_id: string;
  name?: string;
  description?: string;
  [key: string]: any;
}

const Scenarios: React.FC = () => {
  const currentUser = useSelector((state: RootState) => state.auth.user);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editedFields, setEditedFields] = useState<Record<string, any>>({});
  const [isCloning, setIsCloning] = useState(false);
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchScenarios = async () => {
      setIsLoading(true);
      try {
        const response = await scenarioAPI.list();
        const items = Array.isArray(response.data) ? response.data : [];
        setScenarios(items);
        if (items.length > 0) {
          setSelectedScenario(items[0]);
        }
      } catch (err) {
        setError('Failed to load scenarios');
        console.error(err);
      } finally {
        setIsLoading(false);
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
      setIsCloning(false);
      setIsCreatingNew(false);
      setError(null);
    } catch (err) {
      setError('Failed to load scenario details');
      console.error(err);
    }
  };

  const handleCreateNew = () => {
    // Create an empty scenario template
    const emptyScenario: Scenario = {
      scenario_id: `new_scenario_${Date.now()}`,
      name: 'New Scenario',
      description: '',
      setting: '',
      dungeon_master_behaviour: '',
      player_name: '',
      role: '',
      initial_location: '',
      visibility: 'public',
      author: currentUser?.userId || 'unknown',
      version: 1
    };

    setSelectedScenario(emptyScenario);
    setEditedFields({});
    setEditMode(true);
    setIsCreatingNew(true);
    setIsCloning(false);
    setError(null);
  };

  const handleEdit = () => {
    if (!selectedScenario) return;

    // Check if scenario is not owned by current user
    if (selectedScenario.author !== currentUser?.userId) {
      // Clone mode: change author to current user and append to name
      const currentName = selectedScenario.name || selectedScenario.scenario_id;
      setIsCloning(true);
      setEditedFields({
        author: currentUser?.userId || 'unknown',
        name: `${currentName} - cloned by ${currentUser?.userId || 'unknown'}`
      });
    } else {
      setIsCloning(false);
      setEditedFields({});
    }

    setEditMode(true);
  };

  const handleFieldEdit = (fieldName: string, value: any) => {
    setEditedFields(prev => ({ ...prev, [fieldName]: value }));
  };

  const handleSave = async () => {
    if (!selectedScenario) return;

    try {
      // Increment version number if numeric (only for updates, not new scenarios)
      let newVersion = editedFields.version;
      if (!isCreatingNew && newVersion === undefined && selectedScenario.version !== undefined) {
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

      if (isCloning || isCreatingNew) {
        // Create a new scenario (clone or brand new)
        const { _id, ...scenarioWithoutId } = selectedScenario;
        const newScenarioData = {
          ...scenarioWithoutId,
          ...updateData,
          scenario_id: isCreatingNew
            ? (updateData.scenario_id || selectedScenario.scenario_id)
            : `${selectedScenario.scenario_id}_${currentUser?.userId || 'user'}_${Date.now()}`,
          author: updateData.author || currentUser?.userId || 'unknown'
        };

        await scenarioAPI.create(newScenarioData);

        // Refresh the scenario list to show the new scenario
        const scenariosResponse = await scenarioAPI.list();
        setScenarios(scenariosResponse.data ?? []);

        // Select the newly created scenario
        const response = await scenarioAPI.get(newScenarioData.scenario_id);
        setSelectedScenario(response.data);
      } else {
        // Update existing scenario
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
      }

      setEditMode(false);
      setEditedFields({});
      setIsCloning(false);
      setIsCreatingNew(false);
      setError(null);
    } catch (err) {
      setError((isCloning || isCreatingNew) ? 'Failed to create scenario' : 'Failed to save scenario');
      console.error(err);
    }
  };

  const handleDiscard = () => {
    setEditMode(false);
    setEditedFields({});
    setIsCloning(false);
    setIsCreatingNew(false);
    setError(null);

    // If discarding a new scenario, clear the selection
    if (isCreatingNew) {
      setSelectedScenario(null);
    }
  };

  const getFieldValue = (fieldName: string) => {
    if (editedFields.hasOwnProperty(fieldName)) {
      return editedFields[fieldName];
    }
    return selectedScenario?.[fieldName] ?? '';
  };

  if (isLoading) {
    return (
      <div className="main-content scenarios-container">
        <div className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <LoadingIndicator message="Loading scenarios..." />
        </div>
      </div>
    );
  }

  return (
    <div className="main-content scenarios-container">
      <div className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h1 style={{ margin: 0 }}>Scenario Repository</h1>
            <p className="scenarios-description" style={{ margin: '0.25rem 0 0 0' }}>
              Inspect available mission frameworks and their metadata.
            </p>
          </div>
          <button className="primary" onClick={handleCreateNew}>
            Create New
          </button>
        </div>
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
                        {isCreatingNew ? 'Create' : isCloning ? 'Create Copy' : 'Save'}
                      </button>
                      <button className="primary scenario-discard-button" onClick={handleDiscard}>
                        {isCreatingNew ? 'Cancel' : 'Discard'}
                      </button>
                    </div>
                  ) : (
                    <button className="primary scenario-edit-button" onClick={handleEdit}>
                      Edit
                    </button>
                  )}
                </div>

                <div className="scenario-fields">
                  {/* Scenario ID */}
                  <div>
                    <strong className="scenario-field-label">Scenario ID</strong>
                    {isCreatingNew ? (
                      <input
                        type="text"
                        className="scenario-input"
                        value={getFieldValue('scenario_id')}
                        onChange={(e) => handleFieldEdit('scenario_id', e.target.value)}
                        placeholder="unique_scenario_id"
                      />
                    ) : (
                      <div className="scenario-field-value">{selectedScenario.scenario_id}</div>
                    )}
                  </div>

                  {/* Name (editable when creating new) */}
                  <div>
                    <strong className="scenario-field-label">Name</strong>
                    {isCreatingNew ? (
                      <input
                        type="text"
                        className="scenario-input"
                        value={getFieldValue('name')}
                        onChange={(e) => handleFieldEdit('name', e.target.value)}
                        placeholder="Scenario Name"
                      />
                    ) : (
                      <div className="scenario-field-value">{selectedScenario.name}</div>
                    )}
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

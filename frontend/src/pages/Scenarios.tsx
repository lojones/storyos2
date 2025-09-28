import React, { useEffect, useState } from 'react';
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
    } catch (err) {
      setError('Failed to load scenario details');
      console.error(err);
    }
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
                <h2>{selectedScenario.name ?? selectedScenario.scenario_id}</h2>
                <p style={{ opacity: 0.8 }}>{selectedScenario.description ?? 'No description available.'}</p>
                <div style={{ marginTop: '1.5rem' }}>
                  <strong>Configuration</strong>
                  <pre style={{
                    background: 'rgba(15, 23, 42, 0.5)',
                    padding: '1rem',
                    borderRadius: '0.75rem',
                    overflowX: 'auto'
                  }}>
{JSON.stringify(selectedScenario, null, 2)}
                  </pre>
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

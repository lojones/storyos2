import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { gameAPI, scenarioAPI } from '../api/client';
import type { Scenario } from '../types';

const NewGame: React.FC = () => {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        const response = await scenarioAPI.list();
        setScenarios(response.data ?? []);
      } catch (err) {
        setError('Failed to load scenarios');
        console.error(err);
      }
    };
    fetchScenarios();
  }, []);

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selected) {
      setError('Please choose a scenario');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await gameAPI.createSession(selected);
      const sessionId = response.data.session_id;
      navigate(`/game/${sessionId}`);
    } catch (err) {
      setError('Unable to create game session');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="main-content" style={{ maxWidth: '720px', margin: '0 auto' }}>
      <div className="panel">
        <h1>Launch New Mission</h1>
        <p style={{ opacity: 0.7 }}>
          Choose a narrative blueprint to initialise a fresh game session.
        </p>
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <label>
            <div>Scenario</div>
            <select value={selected} onChange={(event) => setSelected(event.target.value)}>
              <option value="">Select a scenario…</option>
              {scenarios.map((scenario) => (
                <option key={scenario.scenario_id} value={scenario.scenario_id}>
                  {scenario.name ?? scenario.scenario_id}
                </option>
              ))}
            </select>
          </label>
          {selected && (
            <div className="card">
              <strong>Briefing</strong>
              <p style={{ opacity: 0.8 }}>
                {scenarios.find((item) => item.scenario_id === selected)?.description ?? 'No description available.'}
              </p>
            </div>
          )}
          {error && <div style={{ color: '#f87171' }}>{error}</div>}
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button className="primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Launching…' : 'Launch Mission'}
            </button>
            <button className="primary" type="button" onClick={() => navigate('/')}
              style={{ background: 'rgba(148, 163, 184, 0.2)' }}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewGame;

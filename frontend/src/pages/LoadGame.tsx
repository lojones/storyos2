import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { gameAPI } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import { GameSessionSummary } from '../types';
import LoadingIndicator from '../components/LoadingIndicator';

const LoadGame: React.FC = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [sessions, setSessions] = useState<GameSessionSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    const fetchSessions = async () => {
      setIsLoading(true);
      try {
        const response = await gameAPI.getUserSessions();
        setSessions(response.data.sessions ?? []);
      } catch (err) {
        setError('Unable to load saved sessions');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchSessions();
  }, [token]);

  if (isLoading) {
    return (
      <div className="main-content" style={{ maxWidth: '860px', margin: '0 auto' }}>
        <div className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <LoadingIndicator message="Loading saved games..." />
        </div>
      </div>
    );
  }

  return (
    <div className="main-content" style={{ maxWidth: '860px', margin: '0 auto' }}>
      <div className="panel">
        <h1>Resume Narrative</h1>
        <p style={{ opacity: 0.7 }}>Select a saved session to continue your adventure.</p>
        {error && <div style={{ color: '#f87171', marginBottom: '1rem' }}>{error}</div>}
        <div className="flex-row">
          {sessions.length === 0 && <div>No sessions found. Launch a new mission first.</div>}
          {sessions.map((session) => {
            const lastEvent = session.timeline && session.timeline.length > 0
              ? session.timeline[session.timeline.length - 1]
              : null;

            return (
              <div key={session._id} className="card" style={{ flex: '1 1 240px' }}>
                <h3>{session.name ?? session.scenario_id}</h3>
                <p style={{ opacity: 0.7 }}>
                  {lastEvent ? lastEvent.event_title : `Scenario: ${session.scenario_id}`}
                </p>
                <p style={{ opacity: 0.6 }}>
                  Last updated:{' '}
                  {session.last_updated
                    ? new Date(session.last_updated).toLocaleString()
                    : 'Unknown'}
                </p>
                <button className="primary" onClick={() => navigate(`/game/${session._id}`)}>
                  Enter Session
                </button>
              </div>
            );
          })}
        </div>
        <button className="primary" style={{ marginTop: '2rem' }} onClick={() => navigate('/')}>Back</button>
      </div>
    </div>
  );
};

export default LoadGame;

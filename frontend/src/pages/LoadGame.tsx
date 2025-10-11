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
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);
  const [deleteResult, setDeleteResult] = useState<{ chatDeleted: boolean; vizDeleted: boolean } | null>(null);
  const [confirmDeleteSessionId, setConfirmDeleteSessionId] = useState<string | null>(null);

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

  const handleDeleteSession = async (sessionId: string) => {
    setDeletingSessionId(sessionId);
    setConfirmDeleteSessionId(null);
    setError(null);

    try {
      const response = await gameAPI.deleteSession(sessionId);
      const result = response.data;

      // Remove the session from the list
      setSessions((prevSessions) => prevSessions.filter((s) => s._id !== sessionId));

      // Show deletion result modal
      setDeleteResult({
        chatDeleted: result.chat_deleted === 'True' || result.chat_deleted === true,
        vizDeleted: result.visualizations_deleted === 'True' || result.visualizations_deleted === true
      });
    } catch (err) {
      setError('Failed to delete session');
      console.error(err);
    } finally {
      setDeletingSessionId(null);
    }
  };

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
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <button className="primary" onClick={() => navigate(`/game/${session._id}`)}>
                    Enter Session
                  </button>
                  <button
                    onClick={() => setConfirmDeleteSessionId(session._id)}
                    disabled={deletingSessionId === session._id}
                    style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '50%',
                      border: 'none',
                      background: 'linear-gradient(135deg, #f00b89ff 0%, #6117a6ff 100%)',
                      color: 'white',
                      fontSize: '18px',
                      fontWeight: 'bold',
                      cursor: deletingSessionId === session._id ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      padding: 0,
                      opacity: deletingSessionId === session._id ? 0.5 : 0.8,
                      transition: 'opacity 0.2s, transform 0.2s',
                      flexShrink: 0
                    }}
                    onMouseEnter={(e) => {
                      if (deletingSessionId !== session._id) {
                        e.currentTarget.style.opacity = '1';
                        e.currentTarget.style.transform = 'scale(1.1)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.opacity = '0.8';
                      e.currentTarget.style.transform = 'scale(1)';
                    }}
                    title="Delete session"
                  >
                    ×
                  </button>
                </div>
              </div>
            );
          })}
        </div>
        <button className="primary" style={{ marginTop: '2rem' }} onClick={() => navigate('/')}>Back</button>
      </div>

      {/* Confirmation Modal */}
      {confirmDeleteSessionId && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
          onClick={() => setConfirmDeleteSessionId(null)}
        >
          <div
            className="panel"
            style={{
              maxWidth: '400px',
              margin: '1rem',
              padding: '2rem',
              border: '2px solid #9333ea',
              boxShadow: '0 0 30px rgba(147, 51, 234, 0.3)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ marginTop: 0, color: '#c084fc' }}>Confirm Deletion</h2>
            <p style={{ marginBottom: '1.5rem' }}>
              Are you sure you want to delete this session? This will permanently remove:
            </p>
            <ul style={{ marginBottom: '1.5rem', paddingLeft: '1.5rem' }}>
              <li>The game session</li>
              <li>All chat messages</li>
              <li>All visualizations</li>
            </ul>
            <p style={{ color: '#f87171', fontWeight: 'bold', marginBottom: '1.5rem' }}>
              This action cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setConfirmDeleteSessionId(null)}
                style={{
                  flex: 1,
                  padding: '0.75rem 1.5rem',
                  background: 'rgba(255, 255, 255, 0.1)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '4px',
                  color: 'white',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteSession(confirmDeleteSessionId)}
                style={{
                  flex: 1,
                  padding: '0.75rem 1.5rem',
                  background: 'linear-gradient(135deg, #f00b89ff 0%, #6117a6ff 100%)',
                  border: 'none',
                  borderRadius: '4px',
                  color: 'white',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  fontWeight: 'bold',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'scale(1.05)';
                  e.currentTarget.style.boxShadow = '0 0 20px rgba(240, 11, 137, 0.5)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Deletion Result Modal */}
      {deleteResult && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
          onClick={() => setDeleteResult(null)}
        >
          <div
            className="panel"
            style={{
              maxWidth: '400px',
              margin: '1rem',
              padding: '2rem'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ marginTop: 0 }}>Session Deleted</h2>
            <p>The game session has been successfully deleted.</p>
            <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem' }}>
              <p style={{ margin: '0.5rem 0' }}>
                <strong>Chat messages:</strong> {deleteResult.chatDeleted ? 'Deleted' : 'None found'}
              </p>
              <p style={{ margin: '0.5rem 0' }}>
                <strong>Visualizations:</strong> {deleteResult.vizDeleted ? 'Deleted' : 'None found'}
              </p>
            </div>
            <button
              className="primary"
              onClick={() => setDeleteResult(null)}
              style={{ width: '100%' }}
            >
              OK
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default LoadGame;

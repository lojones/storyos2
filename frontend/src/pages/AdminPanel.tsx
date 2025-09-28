import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';

interface AdminStats {
  users: number;
  scenarios: number;
  active_sessions: number;
}

const AdminPanel: React.FC = () => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await apiClient.get('/admin/stats');
        setStats(response.data);
      } catch (err) {
        setError('Unable to fetch system stats');
        console.error(err);
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="main-content" style={{ maxWidth: '720px', margin: '0 auto' }}>
      <div className="panel">
        <h1>Control Room</h1>
        <p style={{ opacity: 0.7 }}>Monitor user activity and scenario availability.</p>
        {error && <div style={{ color: '#f87171', marginBottom: '1rem' }}>{error}</div>}
        {stats ? (
          <div className="flex-row" style={{ marginTop: '2rem' }}>
            <div className="card" style={{ flex: '1 1 200px' }}>
              <h3>👥 Users</h3>
              <p style={{ fontSize: '2.5rem', margin: 0 }}>{stats.users}</p>
            </div>
            <div className="card" style={{ flex: '1 1 200px' }}>
              <h3>📚 Scenarios</h3>
              <p style={{ fontSize: '2.5rem', margin: 0 }}>{stats.scenarios}</p>
            </div>
            <div className="card" style={{ flex: '1 1 200px' }}>
              <h3>🎮 Active Sessions</h3>
              <p style={{ fontSize: '2.5rem', margin: 0 }}>{stats.active_sessions}</p>
            </div>
          </div>
        ) : (
          <p>Loading stats…</p>
        )}
      </div>
    </div>
  );
};

export default AdminPanel;

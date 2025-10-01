import React from 'react';
import { useNavigate } from 'react-router-dom';
import { logout } from '../store/slices/authSlice';
import { useAppDispatch, useAuth } from '../hooks/useAuth';

const MainMenu: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { user, role } = useAuth();

  return (
    <div className="main-content">
      <div className="panel" style={{ maxWidth: '960px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1>StoryOS Command Deck</h1>
            <p style={{ opacity: 0.7 }}>Launch and manage narrative simulations with precision.</p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div className="badge">
              <span>🧑‍🚀</span>
              <span>{user?.userId ?? 'Unknown Agent'}</span>
            </div>
            <button
              className="primary"
              style={{ marginTop: '0.75rem' }}
              onClick={() => {
                dispatch(logout());
                navigate('/login', { replace: true });
              }}
            >
              Sign Out
            </button>
          </div>
        </div>

        <div className="section-title" style={{ marginTop: '2.5rem' }}>
          Campaign Operations
        </div>
        <div className="flex-row">
          <div className="card" style={{ flex: '1 1 240px' }}>
            <h3>🎮 Continue Adventures</h3>
            <p>Jump back into an ongoing narrative with full state fidelity.</p>
            <button className="primary" onClick={() => navigate('/load-game')}>
              Load Game
            </button>
          </div>
          <div className="card" style={{ flex: '1 1 240px' }}>
            <h3>🧭 Initiate New Scenario</h3>
            <p>Seed a new mission using approved scenario templates.</p>
            <button className="primary" onClick={() => navigate('/new-game')}>
              New Game
            </button>
          </div>
          <div className="card" style={{ flex: '1 1 240px' }}>
            <h3>📚 Scenario Vault</h3>
            <p>Inspect and refine the available mission blueprints.</p>
            <button className="primary" onClick={() => navigate('/scenarios')}>
              Manage Scenarios
            </button>
          </div>
          {role === 'admin' && (
            <div className="card" style={{ flex: '1 1 240px' }}>
              <h3>🛠️ Control Room</h3>
              <p>View system metrics and administer operator permissions.</p>
              <button className="primary" onClick={() => navigate('/admin')}>
                Admin Panel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MainMenu;

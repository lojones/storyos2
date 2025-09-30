import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { apiClient, adminAPI } from '../api/client';

interface AdminStats {
  users: number;
  scenarios: number;
  active_sessions: number;
}

interface PendingUser {
  user_id: string;
  role: string;
  created_at?: string;
}

interface SystemPrompt {
  _id: string;
  name: string;
  content: string;
  active: boolean;
  version?: number;
  prompt_type?: string;
}

const AdminPanel: React.FC = () => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([]);
  const [storyPrompt, setStoryPrompt] = useState<SystemPrompt | null>(null);
  const [visualizationPrompt, setVisualizationPrompt] = useState<SystemPrompt | null>(null);
  const [editingPrompt, setEditingPrompt] = useState<'story' | 'visualization' | null>(null);
  const [editedContent, setEditedContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [statsResponse, pendingResponse, promptsResponse] = await Promise.all([
        apiClient.get('/admin/stats'),
        adminAPI.getPendingUsers(),
        adminAPI.getSystemPrompts()
      ]);
      setStats(statsResponse.data);
      setPendingUsers(pendingResponse.data);
      setStoryPrompt(promptsResponse.data.story_prompt);
      setVisualizationPrompt(promptsResponse.data.visualization_prompt);
      setError(null);
    } catch (err) {
      setError('Unable to fetch admin data');
      console.error(err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApproveUser = async (userId: string, newRole: string) => {
    setError(null);
    setSuccessMessage(null);
    try {
      await adminAPI.updateUserRole(userId, newRole);
      setSuccessMessage(`User ${userId} has been approved as ${newRole}`);
      // Refresh data
      await fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update user role');
      console.error(err);
    }
  };

  const handleEditPrompt = (type: 'story' | 'visualization') => {
    const prompt = type === 'story' ? storyPrompt : visualizationPrompt;
    if (prompt) {
      setEditingPrompt(type);
      setEditedContent(prompt.content);
    }
  };

  const handleSavePrompt = async () => {
    if (!editingPrompt) return;
    setError(null);
    setSuccessMessage(null);
    try {
      if (editingPrompt === 'story') {
        const response = await adminAPI.updateStoryPrompt(editedContent);
        setStoryPrompt(response.data);
        setSuccessMessage('Story system prompt updated successfully');
      } else {
        const response = await adminAPI.updateVisualizationPrompt(editedContent);
        setVisualizationPrompt(response.data);
        setSuccessMessage('Visualization system prompt updated successfully');
      }
      setEditingPrompt(null);
      setEditedContent('');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update system prompt');
      console.error(err);
    }
  };

  const handleCancelEdit = () => {
    setEditingPrompt(null);
    setEditedContent('');
    setError(null);
  };

  return (
    <div className="main-content" style={{ maxWidth: '980px', margin: '0 auto' }}>
      <div className="panel">
        <h1>Control Room</h1>
        <p style={{ opacity: 0.7 }}>Monitor user activity and scenario availability.</p>

        {error && (
          <div style={{ color: '#f87171', marginBottom: '1rem', padding: '0.75rem', background: 'rgba(248, 113, 113, 0.1)', borderRadius: '0.5rem' }}>
            {error}
          </div>
        )}

        {successMessage && (
          <div style={{ color: '#10b981', marginBottom: '1rem', padding: '0.75rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '0.5rem' }}>
            {successMessage}
          </div>
        )}

        {/* Stats */}
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

        {/* Pending Users Section */}
        {pendingUsers.length > 0 && (
          <div style={{ marginTop: '3rem' }}>
            <h2 style={{ marginBottom: '1rem' }}>Pending User Approvals</h2>
            <p style={{ opacity: 0.7, marginBottom: '1.5rem' }}>
              The following users are awaiting approval to access StoryOS.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {pendingUsers.map((user) => (
                <div key={user.user_id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem' }}>
                  <div>
                    <div style={{ fontWeight: '600', fontSize: '1.1rem' }}>{user.user_id}</div>
                    {user.created_at && (
                      <div style={{ fontSize: '0.875rem', opacity: 0.6, marginTop: '0.25rem' }}>
                        Registered: {new Date(user.created_at).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <button
                      className="primary"
                      onClick={() => handleApproveUser(user.user_id, 'user')}
                      style={{ padding: '0.5rem 1rem', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
                    >
                      Approve as User
                    </button>
                    <button
                      className="primary"
                      onClick={() => handleApproveUser(user.user_id, 'admin')}
                      style={{ padding: '0.5rem 1rem', background: 'linear-gradient(135deg, #f59e0b, #d97706)' }}
                    >
                      Approve as Admin
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* System Prompts Section */}
        <div style={{ marginTop: '3rem' }}>
          <h2 style={{ marginBottom: '1rem' }}>System Prompts</h2>
          <p style={{ opacity: 0.7, marginBottom: '1.5rem' }}>
            Manage the AI system prompts for story generation and visualization.
          </p>

          {/* Story System Prompt */}
          {storyPrompt && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0 }}>{storyPrompt.name}</h3>
                {editingPrompt !== 'story' && (
                  <button
                    className="primary"
                    onClick={() => handleEditPrompt('story')}
                    style={{ padding: '0.5rem 1rem' }}
                  >
                    Edit
                  </button>
                )}
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', fontSize: '0.875rem', opacity: 0.7 }}>
                <div><strong>Version:</strong> {storyPrompt.version || 'N/A'}</div>
                <div><strong>Active:</strong> {storyPrompt.active ? 'Yes' : 'No'}</div>
                {storyPrompt.prompt_type && <div><strong>Type:</strong> {storyPrompt.prompt_type}</div>}
              </div>

              <div>
                <strong style={{ display: 'block', marginBottom: '0.5rem' }}>Content:</strong>
                {editingPrompt === 'story' ? (
                  <>
                    <textarea
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      style={{
                        width: '100%',
                        minHeight: '300px',
                        padding: '0.75rem',
                        fontFamily: 'monospace',
                        fontSize: '0.9rem',
                        background: 'rgba(15, 23, 42, 0.6)',
                        border: '1px solid rgba(148, 163, 184, 0.2)',
                        borderRadius: '0.5rem',
                        color: '#e2e8f0',
                        resize: 'vertical'
                      }}
                    />
                    <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                      <button className="primary" onClick={handleSavePrompt}>
                        Save Changes
                      </button>
                      <button className="primary" onClick={handleCancelEdit} style={{ background: 'rgba(148, 163, 184, 0.2)' }}>
                        Cancel
                      </button>
                    </div>
                  </>
                ) : (
                  <div style={{
                    padding: '1rem',
                    background: 'rgba(15, 23, 42, 0.6)',
                    borderRadius: '0.5rem',
                    maxHeight: '400px',
                    overflowY: 'auto'
                  }}>
                    <ReactMarkdown>{storyPrompt.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Visualization System Prompt */}
          {visualizationPrompt && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0 }}>{visualizationPrompt.name}</h3>
                {editingPrompt !== 'visualization' && (
                  <button
                    className="primary"
                    onClick={() => handleEditPrompt('visualization')}
                    style={{ padding: '0.5rem 1rem' }}
                  >
                    Edit
                  </button>
                )}
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', fontSize: '0.875rem', opacity: 0.7 }}>
                <div><strong>Version:</strong> {visualizationPrompt.version || 'N/A'}</div>
                <div><strong>Active:</strong> {visualizationPrompt.active ? 'Yes' : 'No'}</div>
                {visualizationPrompt.prompt_type && <div><strong>Type:</strong> {visualizationPrompt.prompt_type}</div>}
              </div>

              <div>
                <strong style={{ display: 'block', marginBottom: '0.5rem' }}>Content:</strong>
                {editingPrompt === 'visualization' ? (
                  <>
                    <textarea
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      style={{
                        width: '100%',
                        minHeight: '300px',
                        padding: '0.75rem',
                        fontFamily: 'monospace',
                        fontSize: '0.9rem',
                        background: 'rgba(15, 23, 42, 0.6)',
                        border: '1px solid rgba(148, 163, 184, 0.2)',
                        borderRadius: '0.5rem',
                        color: '#e2e8f0',
                        resize: 'vertical'
                      }}
                    />
                    <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                      <button className="primary" onClick={handleSavePrompt}>
                        Save Changes
                      </button>
                      <button className="primary" onClick={handleCancelEdit} style={{ background: 'rgba(148, 163, 184, 0.2)' }}>
                        Cancel
                      </button>
                    </div>
                  </>
                ) : (
                  <div style={{
                    padding: '1rem',
                    background: 'rgba(15, 23, 42, 0.6)',
                    borderRadius: '0.5rem',
                    maxHeight: '400px',
                    overflowY: 'auto'
                  }}>
                    <ReactMarkdown>{visualizationPrompt.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;

import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { login, fetchCurrentUser } from '../store/slices/authSlice';
import { useAppDispatch, useAuth } from '../hooks/useAuth';
import { authAPI } from '../api/client';

const Login: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { token, isLoading, error } = useAuth();
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const redirectPath = (location.state as { from?: Location })?.from?.pathname ?? '/';

  useEffect(() => {
    if (token) {
      navigate(redirectPath, { replace: true });
    }
  }, [token, navigate, redirectPath]);

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!username || !password) {
      setFormError('Username and password are required');
      return;
    }
    setFormError(null);
    setSuccessMessage(null);
    try {
      await dispatch(login({ username, password })).unwrap();
      await dispatch(fetchCurrentUser()).unwrap();
      navigate('/', { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to login';
      setFormError(message);
    }
  };

  const handleRegister = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!username || !password || !confirmPassword) {
      setFormError('All fields are required');
      return;
    }
    if (password !== confirmPassword) {
      setFormError('Passwords do not match');
      return;
    }
    if (password.length < 6) {
      setFormError('Password must be at least 6 characters');
      return;
    }
    setFormError(null);
    setSuccessMessage(null);
    try {
      await authAPI.register(username, password, 'pending');
      setSuccessMessage('Account created successfully! Your account is being reviewed by an administrator. Please try logging in later.');
      setUsername('');
      setPassword('');
      setConfirmPassword('');
      setActiveTab('login');
    } catch (err: any) {
      const message = err?.response?.data?.detail || 'Unable to register';
      setFormError(message);
    }
  };

  return (
    <div className="main-content" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div className="panel" style={{ maxWidth: '420px', width: '100%' }}>
        <h1 style={{ marginBottom: '1rem' }}>StoryOS</h1>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid rgba(148, 163, 184, 0.2)' }}>
          <button
            onClick={() => { setActiveTab('login'); setFormError(null); setSuccessMessage(null); }}
            style={{
              background: 'none',
              border: 'none',
              padding: '0.75rem 1rem',
              cursor: 'pointer',
              borderBottom: activeTab === 'login' ? '2px solid #8b5cf6' : '2px solid transparent',
              color: activeTab === 'login' ? '#e2e8f0' : 'rgba(226, 232, 240, 0.6)',
              fontWeight: activeTab === 'login' ? '600' : '400',
              transition: 'all 0.2s'
            }}
          >
            Sign In
          </button>
          <button
            onClick={() => { setActiveTab('register'); setFormError(null); setSuccessMessage(null); }}
            style={{
              background: 'none',
              border: 'none',
              padding: '0.75rem 1rem',
              cursor: 'pointer',
              borderBottom: activeTab === 'register' ? '2px solid #8b5cf6' : '2px solid transparent',
              color: activeTab === 'register' ? '#e2e8f0' : 'rgba(226, 232, 240, 0.6)',
              fontWeight: activeTab === 'register' ? '600' : '400',
              transition: 'all 0.2s'
            }}
          >
            Register
          </button>
        </div>

        <p style={{ marginBottom: '1.5rem', opacity: 0.75 }}>
          {activeTab === 'login'
            ? 'Enter your credentials to access the StoryOS control center.'
            : 'Create a new account to get started with StoryOS.'}
        </p>

        {successMessage && (
          <div style={{ color: '#10b981', marginBottom: '1rem', padding: '0.75rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '0.5rem' }}>
            {successMessage}
          </div>
        )}

        {/* Login Form */}
        {activeTab === 'login' && (
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <label>
              <div>Username</div>
              <input
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username"
                placeholder="admin"
              />
            </label>
            <label>
              <div>Password</div>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                placeholder="••••••••"
              />
            </label>
            {(formError || error) && (
              <div style={{ color: '#f87171' }}>{formError ?? error}</div>
            )}
            <button className="primary" type="submit" disabled={isLoading}>
              {isLoading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>
        )}

        {/* Register Form */}
        {activeTab === 'register' && (
          <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <label>
              <div>Username</div>
              <input
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username"
                placeholder="Choose a username"
              />
            </label>
            <label>
              <div>Password</div>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="new-password"
                placeholder="At least 6 characters"
              />
            </label>
            <label>
              <div>Confirm Password</div>
              <input
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                autoComplete="new-password"
                placeholder="Re-enter password"
              />
            </label>
            {formError && (
              <div style={{ color: '#f87171' }}>{formError}</div>
            )}
            <button className="primary" type="submit" disabled={isLoading}>
              Create Account
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default Login;

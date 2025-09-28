import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { login, fetchCurrentUser } from '../store/slices/authSlice';
import { useAppDispatch, useAuth } from '../hooks/useAuth';

const Login: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { token, isLoading, error } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const redirectPath = (location.state as { from?: Location })?.from?.pathname ?? '/';

  useEffect(() => {
    if (token) {
      navigate(redirectPath, { replace: true });
    }
  }, [token, navigate, redirectPath]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!username || !password) {
      setFormError('Username and password are required');
      return;
    }
    setFormError(null);
    try {
      await dispatch(login({ username, password })).unwrap();
      await dispatch(fetchCurrentUser()).unwrap();
      navigate('/', { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to login';
      setFormError(message);
    }
  };

  return (
    <div className="main-content" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div className="panel" style={{ maxWidth: '420px', width: '100%' }}>
        <h1 style={{ marginBottom: '1rem' }}>StoryOS Sign In</h1>
        <p style={{ marginBottom: '2rem', opacity: 0.75 }}>
          Enter your credentials to access the StoryOS control center.
        </p>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
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
      </div>
    </div>
  );
};

export default Login;

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import Login from './pages/Login';
import MainMenu from './pages/MainMenu';
import Game from './pages/Game';
import Scenarios from './pages/Scenarios';
import StoryArchitect from './pages/StoryArchitect';
import LoadGame from './pages/LoadGame';
import NewGame from './pages/NewGame';
import AdminPanel from './pages/AdminPanel';
import ProtectedRoute from './components/ProtectedRoute';

const App: React.FC = () => {
  return (
    <div className="app-shell">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainMenu />
            </ProtectedRoute>
          }
        />
        <Route
          path="/game/:sessionId"
          element={
            <ProtectedRoute>
              <Game />
            </ProtectedRoute>
          }
        />
        <Route
          path="/scenarios"
          element={
            <ProtectedRoute>
              <Scenarios />
            </ProtectedRoute>
          }
        />
        <Route
          path="/story-architect"
          element={
            <ProtectedRoute>
              <StoryArchitect />
            </ProtectedRoute>
          }
        />
        <Route
          path="/load-game"
          element={
            <ProtectedRoute>
              <LoadGame />
            </ProtectedRoute>
          }
        />
        <Route
          path="/new-game"
          element={
            <ProtectedRoute>
              <NewGame />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute requireAdmin>
              <AdminPanel />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
};

export default App;

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import { TrackingProvider } from './context/TrackingContext';

// Pages
import Login from './pages/Login';
import Signup from './pages/Signup';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import LiveDetection from './pages/LiveDetection';
import Analytics from './pages/Analytics';
import SessionHistory from './pages/SessionHistory';
import Reports from './pages/Reports';
import Profile from './pages/Profile';
import Settings from './pages/Settings';

const ProtectedRoute = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white">
        <div className="animate-spin h-8 w-8 border-4 border-violet-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return user ? <Outlet /> : <Navigate to="/login" replace />;
};

const App = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          
          <Route element={<ProtectedRoute />}>
            <Route element={
              <TrackingProvider>
                <Layout />
              </TrackingProvider>
            }>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/live" element={<LiveDetection />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/history" element={<SessionHistory />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;

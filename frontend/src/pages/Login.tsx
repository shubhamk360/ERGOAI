import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Activity } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

import { GoogleLogin } from '@react-oauth/google';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      setLoading(true);
      setError('');
      const res = await api.post('/auth/google', { token: credentialResponse.credential });
      await login(res.data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Google Login failed.');
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const res = await api.post('/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      await login(res.data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4 relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-600/20 rounded-full blur-[100px]" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-600/20 rounded-full blur-[100px]" />

      <div className="glass-panel w-full max-w-md p-8 relative z-10">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-tr from-violet-600 to-indigo-500 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-violet-500/30">
            <Activity className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Welcome back</h1>
          <p className="text-slate-400 mt-1 text-sm">Sign in to ERGOAI</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl mb-6 text-sm">
            {error}
          </div>
        )}
        
        <div className="flex justify-center mb-6 w-full">
          <div className="w-full relative flex items-center justify-center overflow-hidden rounded-lg min-h-[40px]">
            <div className="absolute inset-0 z-10 flex items-center justify-center pointer-events-none">
              {!window.location.hostname.includes("localhost") && 
                <span className="text-xs text-slate-500 opacity-50 z-20 whitespace-nowrap px-4 bg-slate-900 border border-slate-700 rounded-md">Requires valid Client ID</span>}
            </div>
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => setError('Google Login failed.')}
              useOneTap
              theme="filled_black"
              shape="rectangular"
              size="large"
            />
          </div>
        </div>

        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-800"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-slate-900/80 text-slate-500">Or continue with username</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field"
              placeholder="Enter your username"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full mt-6"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <p className="text-center text-slate-400 text-sm mt-6">
          Don't have an account?{' '}
          <Link to="/signup" className="text-violet-400 hover:text-violet-300 font-medium transition-colors">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Login;

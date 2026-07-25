import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuthStore } from '../store/authStore';
import { PasswordInput } from '../components/common/PasswordInput';
import { parseApiError } from '../utils/errorUtils';
import toast from 'react-hot-toast';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const { login, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) navigate('/', { replace: true });
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail) {
      setErrorMsg('Please enter your email address');
      return;
    }
    if (!password) {
      setErrorMsg('Please enter your password');
      return;
    }

    setLoading(true);
    try {
      const { data } = await api.post('/auth/login', {
        email: cleanEmail,
        password,
      });

      login(data.access_token, data.refresh_token, data.user);
      if (!rememberMe) {
        sessionStorage.setItem('remember_me', 'false');
      }
      toast.success(`Welcome back, ${data.user.username}!`);
      navigate('/', { replace: true });
    } catch (err: any) {
      const parsed = parseApiError(err, 'Invalid email or password');
      setErrorMsg(parsed);
      toast.error(parsed);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-8">
      <div className="card max-w-md w-full p-8 space-y-6 border-[var(--color-border)] shadow-2xl">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-black text-white font-['Outfit']">Welcome Back</h1>
          <p className="text-gray-400 text-sm">Sign in to your CineMatch AI account</p>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-xl bg-red-950/60 border border-red-800 text-xs text-red-300 font-medium">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (errorMsg) setErrorMsg('');
              }}
              className="input"
              placeholder="you@example.com"
              autoComplete="email"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider">
                Password
              </label>
              <Link to="/forgot-password" className="text-xs text-[var(--color-primary-light)] hover:underline">
                Forgot?
              </Link>
            </div>
            <PasswordInput
              required
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (errorMsg) setErrorMsg('');
              }}
              placeholder="Enter your password"
              autoComplete="current-password"
            />
          </div>

          <div className="flex items-center justify-between text-xs pt-1">
            <label className="flex items-center gap-2 cursor-pointer text-gray-300">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="rounded border-gray-700 bg-[var(--color-surface-2)] text-[var(--color-primary)] focus:ring-[var(--color-primary)]"
              />
              Remember me
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center py-3 font-bold text-sm shadow-lg mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Signing in...
              </span>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="text-center text-xs text-gray-400">
          Don't have an account?{' '}
          <Link to="/register" className="text-[var(--color-primary-light)] font-semibold hover:underline">
            Create Account
          </Link>
        </div>
      </div>
    </div>
  );
};

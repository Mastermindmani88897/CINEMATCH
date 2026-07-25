import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { parseApiError } from '../utils/errorUtils';
import toast from 'react-hot-toast';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail) {
      toast.error('Please enter your email address');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/forgot-password', { email: cleanEmail });
      setSent(true);
      toast.success('Password reset link sent to your email.');
    } catch (err: any) {
      toast.error(parseApiError(err, 'Failed to send reset link'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-8">
      <div className="card max-w-md w-full p-8 space-y-6 border-[var(--color-border)] shadow-2xl">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-black text-white font-['Outfit']">Reset Password</h1>
          <p className="text-gray-400 text-sm">
            {sent
              ? 'Check your inbox for password reset instructions'
              : 'Enter your email address and we will send you a reset link'}
          </p>
        </div>

        {!sent ? (
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center py-3 font-bold text-sm shadow-lg mt-2 disabled:opacity-50"
            >
              {loading ? 'Sending Link...' : 'Send Reset Link'}
            </button>
          </form>
        ) : (
          <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-800 text-xs text-emerald-300 text-center space-y-2">
            <p>We've sent a password reset link to <strong>{email}</strong> if it exists in our system.</p>
          </div>
        )}

        <div className="text-center text-xs text-gray-400">
          Remember your password?{' '}
          <Link to="/login" className="text-[var(--color-primary-light)] font-semibold hover:underline">
            Back to Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};

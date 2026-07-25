import React, { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { PasswordInput } from '../components/common/PasswordInput';
import { parseApiError } from '../utils/errorUtils';
import toast from 'react-hot-toast';

export const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (!token) {
      setErrorMsg('Invalid or missing password reset token');
      return;
    }
    if (newPassword.length < 8) {
      setErrorMsg('Password must be at least 8 characters long');
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMsg('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/reset-password', { token, new_password: newPassword });
      toast.success('Password reset successfully! Please sign in.');
      navigate('/login');
    } catch (err: any) {
      const parsed = parseApiError(err, 'Failed to reset password');
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
          <h1 className="text-3xl font-black text-white font-['Outfit']">Set New Password</h1>
          <p className="text-gray-400 text-sm">Enter your new password below</p>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-xl bg-red-950/60 border border-red-800 text-xs text-red-300 font-medium">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <PasswordInput
            label="New Password"
            required
            value={newPassword}
            onChange={(e) => {
              setNewPassword(e.target.value);
              if (errorMsg) setErrorMsg('');
            }}
            showStrength={true}
            placeholder="At least 8 characters"
            autoComplete="new-password"
          />

          <PasswordInput
            label="Confirm New Password"
            required
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              if (errorMsg) setErrorMsg('');
            }}
            placeholder="Re-enter your new password"
            autoComplete="new-password"
          />

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center py-3 font-bold text-sm shadow-lg mt-2 disabled:opacity-50"
          >
            {loading ? 'Updating Password...' : 'Reset Password'}
          </button>
        </form>

        <div className="text-center text-xs text-gray-400">
          Remembered your password?{' '}
          <Link to="/login" className="text-[var(--color-primary-light)] font-semibold hover:underline">
            Back to Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};

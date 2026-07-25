import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuthStore } from '../store/authStore';
import { PasswordInput } from '../components/common/PasswordInput';
import { parseApiError } from '../utils/errorUtils';
import toast from 'react-hot-toast';

export const RegisterPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string }>({});

  const { isAuthenticated, login } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) navigate('/', { replace: true });
  }, [isAuthenticated, navigate]);

  const validate = (): boolean => {
    const errors: { [key: string]: string } = {};

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      errors.email = 'Email address is required';
    } else if (!/\S+@\S+\.\S+/.test(cleanEmail)) {
      errors.email = 'Please enter a valid email address';
    }

    const cleanUsername = username.trim();
    if (!cleanUsername) {
      errors.username = 'Username is required';
    } else if (!/^[a-zA-Z0-9_]{3,30}$/.test(cleanUsername)) {
      errors.username = 'Username must be 3-30 chars (letters, numbers, underscores only)';
    }

    if (!password) {
      errors.password = 'Password is required';
    } else if (password.length < 8) {
      errors.password = 'Password must be at least 8 characters long';
    }

    if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      const payload = {
        email: email.trim().toLowerCase(),
        username: username.trim().toLowerCase(),
        full_name: fullName.trim() || undefined,
        password,
      };

      // 1. Call Register API
      await api.post('/auth/register', payload);
      toast.success('Account created successfully! Logging you in...');

      // 2. Auto-login upon successful registration
      try {
        const { data: loginData } = await api.post('/auth/login', {
          email: payload.email,
          password: payload.password,
        });
        login(loginData.access_token, loginData.refresh_token, loginData.user);
        navigate('/', { replace: true });
      } catch {
        // Fallback to login page if email verification required
        navigate('/login');
      }
    } catch (err: any) {
      const errMsg = parseApiError(err, 'Registration failed. Please check your credentials.');
      toast.error(errMsg);

      if (errMsg.toLowerCase().includes('email')) {
        setFieldErrors((prev) => ({ ...prev, email: errMsg }));
      } else if (errMsg.toLowerCase().includes('username')) {
        setFieldErrors((prev) => ({ ...prev, username: errMsg }));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-8">
      <div className="card max-w-md w-full p-8 space-y-6 border-[var(--color-border)] shadow-2xl">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-black text-white font-['Outfit']">Create Account</h1>
          <p className="text-gray-400 text-sm">Join CineMatch AI for personalized movie discovery</p>
        </div>

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
                if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: '' });
              }}
              className={`input ${fieldErrors.email ? 'border-red-500' : ''}`}
              placeholder="you@example.com"
              autoComplete="email"
            />
            {fieldErrors.email && <p className="text-xs text-red-400 font-medium mt-1">{fieldErrors.email}</p>}
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1">
              Username
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                if (fieldErrors.username) setFieldErrors({ ...fieldErrors, username: '' });
              }}
              className={`input ${fieldErrors.username ? 'border-red-500' : ''}`}
              placeholder="cinephile99"
              autoComplete="username"
            />
            {fieldErrors.username && <p className="text-xs text-red-400 font-medium mt-1">{fieldErrors.username}</p>}
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1">
              Full Name (Optional)
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="input"
              placeholder="Alex Morgan"
              autoComplete="name"
            />
          </div>

          <PasswordInput
            label="Password"
            required
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: '' });
            }}
            error={fieldErrors.password}
            showStrength={true}
            placeholder="At least 8 characters"
            autoComplete="new-password"
          />

          <PasswordInput
            label="Confirm Password"
            required
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              if (fieldErrors.confirmPassword) setFieldErrors({ ...fieldErrors, confirmPassword: '' });
            }}
            error={fieldErrors.confirmPassword}
            placeholder="Re-enter your password"
            autoComplete="new-password"
          />

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center py-3 font-bold text-sm shadow-lg mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Creating Account...
              </span>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div className="text-center text-xs text-gray-400">
          Already have an account?{' '}
          <Link to="/login" className="text-[var(--color-primary-light)] font-semibold hover:underline">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};

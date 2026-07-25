import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  FilmIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  SunIcon,
  MoonIcon,
  UserIcon,
  ArrowRightOnRectangleIcon,
  AdjustmentsHorizontalIcon,
  ChartBarIcon,
  TrophyIcon,
} from '@heroicons/react/24/outline';
import { useAuthStore } from '../../store/authStore';
import { useThemeStore } from '../../store/themeStore';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 glass border-b border-[var(--color-border)] backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center shadow-lg shadow-[var(--color-primary)]/20 group-hover:scale-105 transition-transform">
            <FilmIcon className="w-6 h-6 text-white" />
          </div>
          <span className="font-extrabold text-xl tracking-tight text-[var(--color-text)] font-['Outfit']">
            Cine<span className="gradient-text">Match</span> AI
          </span>
        </Link>

        {/* Nav Links */}
        <div className="hidden md:flex items-center gap-6">
          <Link
            to="/"
            className={`font-medium transition-colors hover:text-[var(--color-primary-light)] ${
              isActive('/') ? 'text-[var(--color-primary-light)] font-semibold' : 'text-[var(--color-text-muted)]'
            }`}
          >
            Home
          </Link>
          <Link
            to="/recommendations"
            className={`flex items-center gap-1.5 font-medium transition-colors hover:text-[var(--color-accent)] ${
              isActive('/recommendations') ? 'text-[var(--color-accent)] font-semibold' : 'text-[var(--color-text-muted)]'
            }`}
          >
            <SparklesIcon className="w-4 h-4 text-[var(--color-accent)] animate-pulse" />
            AI Recommender
          </Link>
          <Link
            to="/search"
            className={`font-medium transition-colors hover:text-[var(--color-primary-light)] ${
              isActive('/search') ? 'text-[var(--color-primary-light)] font-semibold' : 'text-[var(--color-text-muted)]'
            }`}
          >
            Search
          </Link>
          <Link
            to="/compare"
            className={`flex items-center gap-1 font-medium transition-colors hover:text-[var(--color-text)] ${
              isActive('/compare') ? 'text-[var(--color-text)] font-semibold' : 'text-[var(--color-text-muted)]'
            }`}
          >
            <AdjustmentsHorizontalIcon className="w-4 h-4" />
            Compare
          </Link>
          <Link
            to="/top-rated"
            className={`flex items-center gap-1 font-medium transition-colors hover:text-amber-400 ${
              isActive('/top-rated') ? 'text-amber-400 font-semibold' : 'text-[var(--color-text-muted)]'
            }`}
          >
            <TrophyIcon className="w-4 h-4" />
            Top Rated
          </Link>
          {user?.is_admin && (
            <Link
              to="/admin"
              className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-red-950/60 text-red-400 border border-red-800/40 hover:bg-red-900/60 transition-colors"
            >
              <ChartBarIcon className="w-3.5 h-3.5" />
              Admin
            </Link>
          )}
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-4">
          {/* Quick Search Button */}
          <button
            onClick={() => navigate('/search')}
            className="p-2 rounded-lg bg-[var(--color-surface-2)] text-gray-400 hover:text-white hover:bg-[var(--color-surface-3)] transition-colors"
            title="Search movies"
          >
            <MagnifyingGlassIcon className="w-5 h-5" />
          </button>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg bg-[var(--color-surface-2)] text-gray-400 hover:text-white hover:bg-[var(--color-surface-3)] transition-colors"
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <SunIcon className="w-5 h-5" /> : <MoonIcon className="w-5 h-5" />}
          </button>

          {/* User Auth Menu */}
          {isAuthenticated && user ? (
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 p-1.5 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] hover:border-gray-600 transition-colors"
              >
                <div className="w-8 h-8 rounded-lg bg-[var(--color-primary)] text-white font-bold flex items-center justify-center text-sm uppercase overflow-hidden">
                  {user.avatar_url ? (
                    <img src={user.avatar_url} alt={user.username} className="w-full h-full object-cover" />
                  ) : (
                    user.username.charAt(0)
                  )}
                </div>
                <span className="hidden sm:inline text-sm font-medium text-gray-200">{user.username}</span>
              </button>

              {/* Dropdown Menu */}
              {dropdownOpen && (
                <div
                  className="absolute right-0 mt-2 w-48 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] shadow-2xl py-2 z-50"
                  onMouseLeave={() => setDropdownOpen(false)}
                >
                  <Link
                    to="/profile"
                    onClick={() => setDropdownOpen(false)}
                    className="flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:bg-[var(--color-surface-2)] hover:text-white"
                  >
                    <UserIcon className="w-4 h-4" />
                    My Profile & Taste
                  </Link>
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      logout();
                      navigate('/');
                    }}
                    className="w-full text-left flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-red-950/30 hover:text-red-300"
                  >
                    <ArrowRightOnRectangleIcon className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/login" className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors">
                Sign In
              </Link>
              <Link to="/register" className="btn-primary text-sm px-4 py-2">
                Get Started
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { recApi, userApi } from '../api/client';
import type { TasteAnalysis, Movie } from '../types';
import { MovieCard } from '../components/common/MovieCard';
import { HeartIcon, BookmarkIcon, ClockIcon, ChartPieIcon } from '@heroicons/react/24/solid';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';

const COLORS = ['#e50914', '#f5c518', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899', '#f97316'];

export const ProfilePage: React.FC = () => {
  const { user } = useAuthStore();
  const [taste, setTaste] = useState<TasteAnalysis | null>(null);
  const [favorites, setFavorites] = useState<Movie[]>([]);
  const [watchlist, setWatchlist] = useState<Movie[]>([]);
  const [history, setHistory] = useState<Movie[]>([]);
  const [activeTab, setActiveTab] = useState<'taste' | 'favorites' | 'watchlist' | 'history'>('taste');

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const [t, f, w, h] = await Promise.all([
          recApi.getTasteAnalysis().catch(() => null),
          userApi.getFavorites().catch(() => []),
          userApi.getWatchlist().catch(() => []),
          userApi.getHistory().catch(() => []),
        ]);
        setTaste(t);
        setFavorites(f);
        setWatchlist(w);
        setHistory(h);
      } catch {}
    };
    fetchUserData();
  }, []);

  if (!user) {
    return <div className="text-center py-20 text-gray-400">Please sign in to view your profile.</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="card p-6 sm:p-8 flex flex-col sm:flex-row items-center gap-6 border-[var(--color-primary)]/30">
        <div className="w-24 h-24 rounded-2xl bg-gradient-to-tr from-[var(--color-primary)] to-[var(--color-accent)] text-white font-extrabold text-3xl flex items-center justify-center shadow-xl">
          {user.avatar_url ? (
            <img src={user.avatar_url} alt={user.username} className="w-full h-full object-cover rounded-2xl" />
          ) : (
            user.username.charAt(0).toUpperCase()
          )}
        </div>

        <div className="space-y-1 text-center sm:text-left flex-1">
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
            <h1 className="text-2xl sm:text-3xl font-black text-white font-['Outfit']">{user.username}</h1>
            {user.is_admin && (
              <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-red-950 text-red-400 border border-red-800 font-bold">
                Admin
              </span>
            )}
          </div>
          <p className="text-sm text-gray-400">{user.email}</p>
          <p className="text-xs text-gray-400 pt-1">{user.bio || 'Movie enthusiast exploring cinema through AI.'}</p>
        </div>

        {taste && (
          <div className="card p-4 bg-[var(--color-surface-2)] border-amber-500/30 text-center space-y-1">
            <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest block">AI Movie Personality</span>
            <div className="font-extrabold text-white text-base font-['Outfit']">{taste.personality}</div>
          </div>
        )}
      </div>

      <div className="flex border-b border-[var(--color-border)] gap-6 text-sm font-semibold">
        {[
          { id: 'taste', label: 'AI Taste Analytics', icon: ChartPieIcon },
          { id: 'favorites', label: `Favorites (${favorites.length})`, icon: HeartIcon },
          { id: 'watchlist', label: `Watchlist (${watchlist.length})`, icon: BookmarkIcon },
          { id: 'history', label: `Watch History (${history.length})`, icon: ClockIcon },
        ].map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
                activeTab === t.id
                  ? 'border-[var(--color-primary)] text-[var(--color-primary-light)]'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              <Icon className="w-4 h-4" />
              {t.label}
            </button>
          );
        })}
      </div>

      {activeTab === 'taste' && taste && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="card p-6 space-y-4">
            <h3 className="font-bold text-white text-lg font-['Outfit']">Favorite Genre Distribution</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={taste.favorite_genres}
                    dataKey="count"
                    nameKey="genre"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={(entry: any) => `${entry.genre} ${entry.percentage}%`}
                  >
                    {taste.favorite_genres.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card p-6 space-y-4">
            <h3 className="font-bold text-white text-lg font-['Outfit']">Taste Profile Metrics</h3>
            <div className="grid grid-cols-2 gap-4 text-center">
              <div className="p-4 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)]">
                <div className="text-2xl font-black text-[var(--color-accent)] font-['Outfit']">{taste.average_rating.toFixed(1)}</div>
                <div className="text-xs text-gray-400 mt-1">Average Given Rating</div>
              </div>
              <div className="p-4 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)]">
                <div className="text-2xl font-black text-[var(--color-primary-light)] font-['Outfit']">{taste.favorite_decade}</div>
                <div className="text-xs text-gray-400 mt-1">Favorite Era</div>
              </div>
            </div>

            <div className="pt-2 text-xs text-gray-300 leading-relaxed bg-[var(--color-surface-2)] p-4 rounded-xl border border-[var(--color-border)]">
              <span className="font-bold text-white block mb-1">Personality Insight:</span>
              {taste.personality_description}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'favorites' && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {favorites.map((m) => (
            <MovieCard key={m.id} movie={m} />
          ))}
        </div>
      )}

      {activeTab === 'watchlist' && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {watchlist.map((m) => (
            <MovieCard key={m.id} movie={m} />
          ))}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {history.map((m) => (
            <MovieCard key={m.id} movie={m} />
          ))}
        </div>
      )}
    </div>
  );
};

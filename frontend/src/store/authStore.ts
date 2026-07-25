import { create } from 'zustand';
import type { User } from '../types';
import { api } from '../api/client';
import { useMovieStore } from './movieStore';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (accessToken: string, refreshToken: string, user: User) => void;
  logout: () => void;
  fetchProfile: () => Promise<void>;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: true,

  login: (accessToken, refreshToken, user) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    set({ user, isAuthenticated: true, isLoading: false });
    // Pre-load user's favorites and watchlist into movieStore for instant UI
    _loadUserCollections();
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, isAuthenticated: false, isLoading: false });
    // Clear favorites/watchlist from movieStore
    const { setFavorites, setWatchlist } = useMovieStore.getState();
    setFavorites([]);
    setWatchlist([]);
  },

  fetchProfile: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ user: null, isAuthenticated: false, isLoading: false });
      return;
    }
    try {
      const { data } = await api.get<User>('/auth/me');
      set({ user: data, isAuthenticated: true, isLoading: false });
      // Pre-load favorites/watchlist after profile load
      _loadUserCollections();
    } catch {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  updateUser: (updatedUser) => {
    set((state) => ({
      user: state.user ? { ...state.user, ...updatedUser } : null,
    }));
  },
}));

/** Load favorites and watchlist IDs from the API and sync to movieStore. */
async function _loadUserCollections() {
  try {
    const [favsRes, watchRes] = await Promise.all([
      api.get<any[]>('/users/me/favorites'),
      api.get<any[]>('/users/me/watchlist'),
    ]);
    const { setFavorites, setWatchlist } = useMovieStore.getState();
    setFavorites(favsRes.data.map((m: any) => m.id));
    setWatchlist(watchRes.data.map((m: any) => m.id));
  } catch {
    // Silently fail — user might have no favorites yet
  }
}

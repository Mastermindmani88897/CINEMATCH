import axios from 'axios';
import type {
  Movie, PaginatedResponse, RecommendationResponse,
  SearchSuggestion, RatingResponse, ReviewResponse, NoteResponse
} from '../types';

function getRawApiUrl(): string {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  if (import.meta.env.PROD) {
    return 'https://cinematch-backend-okio.onrender.com';
  }
  return 'http://localhost:8000';
}

const RAW_API_URL = getRawApiUrl();
const API_BASE_URL = RAW_API_URL.endsWith('/api') ? RAW_API_URL : `${RAW_API_URL.replace(/\/$/, '')}/api`;

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken });
          const newAccessToken = res.data.access_token;
          localStorage.setItem('access_token', newAccessToken);
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export const movieApi = {
  getMovies: async (params?: any) => {
    const { data } = await api.get<PaginatedResponse<Movie>>('/movies', { params });
    return data;
  },
  getMovieById: async (id: number) => {
    const { data } = await api.get<Movie>(`/movies/${id}`);
    return data;
  },
  getTrending: async (limit = 20) => {
    const { data } = await api.get<Movie[]>('/movies/trending', { params: { limit } });
    return data;
  },
  getPopular: async (limit = 20) => {
    const { data } = await api.get<Movie[]>('/movies/popular', { params: { limit } });
    return data;
  },
  getTopRated: async (limit = 20) => {
    const { data } = await api.get<Movie[]>('/movies/top-rated', { params: { limit } });
    return data;
  },
  getUpcoming: async (limit = 20) => {
    const { data } = await api.get<Movie[]>('/movies/upcoming', { params: { limit } });
    return data;
  },
  getGenres: async () => {
    const { data } = await api.get<string[]>('/movies/genres');
    return data;
  },
};

export const recApi = {
  getIndustryRecs: async (industry: string, limit = 20) => {
    const { data } = await api.get<RecommendationResponse>(`/recommendations/industry/${industry}`, { params: { limit } });
    return data;
  },
  getPopularRecs: async (mode = 'weighted', limit = 20) => {
    const { data } = await api.get<RecommendationResponse>('/recommendations/popular', { params: { mode, limit } });
    return data;
  },
  getGenreRecs: async (genres: string, limit = 20) => {
    const { data } = await api.get<RecommendationResponse>('/recommendations/genre', { params: { genres, limit } });
    return data;
  },
  getMoodRecs: async (mood: string, limit = 20) => {
    const { data } = await api.get<RecommendationResponse>(`/recommendations/mood/${mood}`, { params: { limit } });
    return data;
  },
  getMoods: async () => {
    const { data } = await api.get<{ moods: string[] }>('/recommendations/moods');
    return data.moods;
  },
  getIndustries: async () => {
    const { data } = await api.get<{ industries: string[] }>('/recommendations/industries');
    return data.industries;
  },
  postSemanticSearch: async (query: string, limit = 20) => {
    const { data } = await api.post<RecommendationResponse>('/recommendations/semantic', { query, limit });
    return data;
  },
};

export const searchApi = {
  search: async (q: string, params?: any) => {
    const { data } = await api.get<PaginatedResponse<Movie>>('/search', { params: { q, ...params } });
    return data;
  },
  getSuggestions: async (q: string) => {
    const { data } = await api.get<SearchSuggestion[]>('/search/suggestions', { params: { q } });
    return data;
  },
  getTrendingSearches: async () => {
    const { data } = await api.get<{ query: string; count: number }[]>('/search/trending-searches');
    return data;
  },
};

export const userApi = {
  getFavorites: async () => {
    const { data } = await api.get<Movie[]>('/users/me/favorites');
    return data;
  },
  addFavorite: async (movieId: number) => {
    const { data } = await api.post(`/users/me/favorites/${movieId}`);
    return data;
  },
  removeFavorite: async (movieId: number) => {
    const { data } = await api.delete(`/users/me/favorites/${movieId}`);
    return data;
  },
  getWatchlist: async () => {
    const { data } = await api.get<Movie[]>('/users/me/watchlist');
    return data;
  },
  addWatchlist: async (movieId: number) => {
    const { data } = await api.post(`/users/me/watchlist/${movieId}`);
    return data;
  },
  removeWatchlist: async (movieId: number) => {
    const { data } = await api.delete(`/users/me/watchlist/${movieId}`);
    return data;
  },
  getHistory: async () => {
    const { data } = await api.get<Movie[]>('/users/me/history');
    return data;
  },
  logHistory: async (movieId: number) => {
    const { data } = await api.post(`/users/me/history/${movieId}`);
    return data;
  },
  clearHistory: async () => {
    const { data } = await api.delete('/users/me/history');
    return data;
  },
  rateMovie: async (movieId: number, rating: number) => {
    const { data } = await api.post<RatingResponse>(`/users/me/ratings/${movieId}`, { rating });
    return data;
  },
  deleteRating: async (movieId: number) => {
    const { data } = await api.delete(`/users/me/ratings/${movieId}`);
    return data;
  },
  getReviews: async (movieId: number) => {
    const { data } = await api.get<ReviewResponse[]>(`/users/movies/${movieId}/reviews`);
    return data;
  },
  createReview: async (movieId: number, content: string, containsSpoilers = false) => {
    const { data } = await api.post<ReviewResponse>(`/users/movies/${movieId}/reviews`, { content, contains_spoilers: containsSpoilers });
    return data;
  },
  getNote: async (movieId: number) => {
    const { data } = await api.get<NoteResponse | null>(`/users/me/notes/${movieId}`);
    return data;
  },
  saveNote: async (movieId: number, content: string) => {
    const { data } = await api.post<NoteResponse>(`/users/me/notes/${movieId}`, { content });
    return data;
  },
};

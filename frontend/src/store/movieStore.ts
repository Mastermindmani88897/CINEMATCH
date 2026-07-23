import { create } from 'zustand';

interface MovieState {
  activeTrailerKey: string | null;
  activeTrailerTitle: string | null;
  favoriteIds: number[];
  watchlistIds: number[];
  openTrailer: (key: string, title: string) => void;
  closeTrailer: () => void;
  setFavorites: (ids: number[]) => void;
  setWatchlist: (ids: number[]) => void;
  toggleFavoriteId: (id: number) => void;
  toggleWatchlistId: (id: number) => void;
}

export const useMovieStore = create<MovieState>((set) => ({
  activeTrailerKey: null,
  activeTrailerTitle: null,
  favoriteIds: [],
  watchlistIds: [],

  openTrailer: (key, title) => set({ activeTrailerKey: key, activeTrailerTitle: title }),
  closeTrailer: () => set({ activeTrailerKey: null, activeTrailerTitle: null }),

  setFavorites: (ids) => set({ favoriteIds: ids }),
  setWatchlist: (ids) => set({ watchlistIds: ids }),

  toggleFavoriteId: (id) =>
    set((state) => ({
      favoriteIds: state.favoriteIds.includes(id)
        ? state.favoriteIds.filter((favId) => favId !== id)
        : [...state.favoriteIds, id],
    })),

  toggleWatchlistId: (id) =>
    set((state) => ({
      watchlistIds: state.watchlistIds.includes(id)
        ? state.watchlistIds.filter((wId) => wId !== id)
        : [...state.watchlistIds, id],
    })),
}));

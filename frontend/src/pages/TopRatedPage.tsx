import React, { useState, useEffect, useCallback } from 'react';
import { TrophyIcon, FunnelIcon, ArrowPathIcon } from '@heroicons/react/24/solid';
import { movieApi } from '../api/client';
import type { Movie } from '../types';
import { MovieCard } from '../components/common/MovieCard';

const PRESETS = [
  { id: 'all_time', label: 'Top Rated All Time' },
  { id: 'top_100', label: 'Top 100 IMDb/TMDB' },
  { id: 'top_250', label: 'Top 250 Cinema Legends' },
  { id: 'top_500', label: 'Top 500 Global Masterpieces' },
  { id: 'top_1000', label: 'Top 1000 Essential Films' },
];

const INDUSTRIES = [
  { id: '', label: 'All Industries' },
  { id: 'hollywood', label: 'Hollywood (EN)' },
  { id: 'bollywood', label: 'Bollywood (HI)' },
  { id: 'tollywood', label: 'Tollywood (TE)' },
  { id: 'kollywood', label: 'Kollywood (TA)' },
  { id: 'mollywood', label: 'Mollywood (ML)' },
  { id: 'sandalwood', label: 'Sandalwood (KN)' },
  { id: 'anime', label: 'Anime / Japanese' },
  { id: 'korean', label: 'Korean Cinema' },
  { id: 'international', label: 'International' },
];

export const TopRatedPage: React.FC = () => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [preset, setPreset] = useState('all_time');
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [selectedYear, setSelectedYear] = useState<number | ''>('');
  const [genres, setGenres] = useState<string[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    movieApi.getGenres().then(setGenres).catch(() => {});
  }, []);

  const fetchTopRated = useCallback(async (resetPage = false) => {
    const targetPage = resetPage ? 1 : page;
    if (resetPage) setLoading(true);
    else setLoadingMore(true);

    try {
      const res = await movieApi.getTopRatedCatalog({
        page: targetPage,
        per_page: 20,
        preset,
        industry: selectedIndustry || undefined,
        genre: selectedGenre || undefined,
        year: selectedYear || undefined,
        min_votes: 10,
      });

      setTotalResults(res.total);
      setTotalPages(res.pages);
      if (resetPage) {
        setMovies(res.items);
        setPage(1);
      } else {
        setMovies((prev) => [...prev, ...res.items]);
      }
    } catch (err) {
      console.error('Failed to load top rated movies', err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [preset, selectedIndustry, selectedGenre, selectedYear, page]);

  useEffect(() => {
    fetchTopRated(true);
  }, [preset, selectedIndustry, selectedGenre, selectedYear]);

  // Infinite Scroll Listener
  useEffect(() => {
    const handleScroll = () => {
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 600) {
        if (!loadingMore && page < totalPages) {
          setPage((prev) => prev + 1);
        }
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [loadingMore, page, totalPages]);

  useEffect(() => {
    if (page > 1) {
      fetchTopRated(false);
    }
  }, [page]);

  const handleResetFilters = () => {
    setPreset('all_time');
    setSelectedIndustry('');
    setSelectedGenre('');
    setSelectedYear('');
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="text-center space-y-3 max-w-3xl mx-auto">
        <h1 className="text-3xl sm:text-5xl font-black text-[var(--color-text)] font-['Outfit'] flex items-center justify-center gap-3">
          <TrophyIcon className="w-10 h-10 text-amber-400" /> Top Rated Movies of All Time
        </h1>
        <p className="text-[var(--color-text-muted)] text-sm sm:text-base">
          Browse the highest-rated films across Hollywood, Bollywood, Tollywood, Anime, and Global Cinema without industry bias.
        </p>
      </div>

      {/* Preset Tabs */}
      <div className="flex flex-wrap items-center justify-center gap-2">
        {PRESETS.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => setPreset(p.id)}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
              preset === p.id
                ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 shadow-lg scale-105'
                : 'card hover:border-amber-500/50 text-[var(--color-text-muted)]'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Industry Filter Chips & Additional Controls */}
      <div className="card p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs font-bold uppercase tracking-wider text-[var(--color-primary-light)] flex items-center gap-1.5">
            <FunnelIcon className="w-4 h-4" /> Filter by Industry:
          </span>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-amber-500 dark:text-amber-400 bg-amber-500/10 px-3 py-1 rounded-full border border-amber-500/30">
              {totalResults.toLocaleString()} Movies Found
            </span>
            {(selectedIndustry || selectedGenre || selectedYear || preset !== 'all_time') && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="btn-ghost text-xs py-1 px-3 flex items-center gap-1"
              >
                <ArrowPathIcon className="w-3.5 h-3.5" /> Reset
              </button>
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {INDUSTRIES.map((ind) => (
            <button
              key={ind.id}
              type="button"
              onClick={() => setSelectedIndustry(ind.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                selectedIndustry === ind.id
                  ? 'bg-[var(--color-primary)] text-white shadow-md'
                  : 'bg-[var(--color-surface-2)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] border border-[var(--color-border)]'
              }`}
            >
              {ind.label}
            </button>
          ))}
        </div>

        {/* Secondary Filter Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2 border-t border-[var(--color-border)]">
          <div>
            <label className="text-[11px] font-semibold text-[var(--color-text-dim)] uppercase block mb-1">Genre</label>
            <select
              value={selectedGenre}
              onChange={(e) => setSelectedGenre(e.target.value)}
              className="input text-xs bg-[var(--color-surface-2)]"
            >
              <option value="">All Genres</option>
              {genres.map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-[var(--color-text-dim)] uppercase block mb-1">Release Year</label>
            <input
              type="number"
              placeholder="e.g. 2023"
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value ? parseInt(e.target.value) : '')}
              className="input text-xs bg-[var(--color-surface-2)]"
            />
          </div>
        </div>
      </div>

      {/* Movies Grid */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
          {Array.from({ length: 15 }).map((_, i) => (
            <div key={i} className="skeleton aspect-[2/3] rounded-2xl" />
          ))}
        </div>
      ) : movies.length > 0 ? (
        <div className="space-y-8">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
            {movies.map((m, index) => (
              <div key={`${m.id}-${index}`} className="relative group">
                <div className="absolute top-2 left-2 z-10 px-2 py-0.5 rounded-md bg-amber-500 text-slate-950 font-black text-xs shadow-lg">
                  #{index + 1}
                </div>
                <MovieCard movie={m} />
              </div>
            ))}
          </div>

          {loadingMore && (
            <div className="text-center py-6">
              <div className="inline-block w-8 h-8 border-4 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
      ) : (
        <div className="card p-12 text-center space-y-4 max-w-md mx-auto">
          <div className="text-5xl">🏆</div>
          <h3 className="text-xl font-bold text-[var(--color-text)] font-['Outfit']">No Top Rated Movies Found</h3>
          <p className="text-xs text-[var(--color-text-muted)]">
            Try adjusting your filters or resetting to view all top rated cinema.
          </p>
          <button type="button" onClick={handleResetFilters} className="btn-primary text-xs py-2 px-4">
            Reset Filters
          </button>
        </div>
      )}
    </div>
  );
};

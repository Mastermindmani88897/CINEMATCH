import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SearchBar } from '../components/common/SearchBar';
import { MovieCard } from '../components/common/MovieCard';
import { MovieGridSkeleton } from '../components/common/Skeleton';
import { searchApi, recApi, movieApi } from '../api/client';
import type { Movie, RecommendationItem } from '../types';
import { FunnelIcon, SparklesIcon, ArrowPathIcon, XMarkIcon, CheckIcon } from '@heroicons/react/24/outline';

export const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [isSemantic, setIsSemantic] = useState(false);
  const [movies, setMovies] = useState<Movie[]>([]);
  const [semanticResults, setSemanticResults] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [availableGenres, setAvailableGenres] = useState<string[]>([]);
  
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Multi-select and combined filter state
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState(searchParams.get('language') || '');
  const [minRating, setMinRating] = useState('0');
  const [sortBy, setSortBy] = useState('popularity');

  const query = searchParams.get('q') || '';

  useEffect(() => {
    movieApi.getGenres().then(setAvailableGenres).catch(console.error);
  }, []);

  useEffect(() => {
    const langFromUrl = searchParams.get('language');
    if (langFromUrl !== null && langFromUrl !== selectedLanguage) {
      setSelectedLanguage(langFromUrl);
    }
  }, [searchParams]);

  // Trigger new search whenever query or any combined filter changes
  useEffect(() => {
    setPage(1);
    executeSearch(query, 1, false);
  }, [query, selectedGenres, selectedYear, selectedLanguage, minRating, sortBy, isSemantic]);

  // Infinite Scroll Listener
  useEffect(() => {
    const handleScroll = () => {
      if (loading || loadingMore || page >= totalPages) return;
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 600) {
        handleLoadMore();
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [page, totalPages, loading, loadingMore]);

  const executeSearch = async (searchQuery: string, pageNum: number, append: boolean) => {
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

    try {
      if (isSemantic && searchQuery.trim()) {
        const res = await recApi.postSemanticSearch(searchQuery, 40);
        setSemanticResults(res.recommendations);
        setMovies([]);
        setTotal(res.total);
        setTotalPages(1);
      } else {
        const params: any = {
          page: pageNum,
          per_page: 24,
          sort: sortBy,
          min_rating: parseFloat(minRating),
        };
        if (selectedGenres.length > 0) params.genres = selectedGenres.join(',');
        if (selectedYear) params.year = parseInt(selectedYear);
        if (selectedLanguage) params.language = selectedLanguage;

        const res = searchQuery.trim()
          ? await searchApi.search(searchQuery, params)
          : await movieApi.getMovies(params);

        if (append) {
          setMovies((prev) => {
            const existingIds = new Set(prev.map((m) => m.id));
            const newUnique = res.items.filter((m) => !existingIds.has(m.id));
            return [...prev, ...newUnique];
          });
        } else {
          setMovies(res.items);
        }

        setSemanticResults([]);
        setTotal(res.total);
        setTotalPages(res.pages);
      }
    } catch (err) {
      console.error('Search failed', err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleLoadMore = () => {
    if (page < totalPages && !loadingMore) {
      const nextPage = page + 1;
      setPage(nextPage);
      executeSearch(query, nextPage, true);
    }
  };

  const toggleGenre = (genreName: string) => {
    setSelectedGenres((prev) =>
      prev.includes(genreName) ? prev.filter((g) => g !== genreName) : [...prev, genreName]
    );
  };

  const handleClearFilters = () => {
    setSelectedGenres([]);
    setSelectedYear('');
    setSelectedLanguage('');
    setMinRating('0');
    setSortBy('popularity');
  };

  const activeFilterCount =
    selectedGenres.length +
    (selectedYear ? 1 : 0) +
    (selectedLanguage ? 1 : 0) +
    (minRating !== '0' ? 1 : 0);

  const handleSearchSubmit = (newQuery: string) => {
    setSearchParams({ q: newQuery });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="space-y-4 max-w-3xl mx-auto text-center">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-[var(--color-text)] font-['Outfit']">
          Search & Discover Movies
        </h1>
        <SearchBar
          autoFocus
          placeholder={isSemantic ? 'Ask AI e.g. "movies about space travel or futuristic technology"' : 'Search title, director, cast, Tollywood, Bollywood...'}
          onSearchSubmit={handleSearchSubmit}
        />

        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            type="button"
            onClick={() => setIsSemantic(!isSemantic)}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold transition-all border ${
              isSemantic
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 border-indigo-400 text-white shadow-lg shadow-indigo-500/30'
                : 'bg-[var(--color-surface-2)] border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
            }`}
          >
            <SparklesIcon className="w-4 h-4" />
            {isSemantic ? 'Semantic Natural Language Search ON' : 'Switch to Semantic AI Search'}
          </button>
        </div>
      </div>

      {/* Multi-Select & Combined Filter Panel */}
      <div className="card p-6 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-3">
            <FunnelIcon className="w-5 h-5 text-[var(--color-primary)]" />
            <span className="text-base font-bold text-[var(--color-text)] font-['Outfit']">Multi-Select Filters</span>
            {activeFilterCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full bg-[var(--color-primary)]/20 text-[var(--color-primary-light)] border border-[var(--color-primary)]/40 text-xs font-extrabold">
                {activeFilterCount} Active
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {activeFilterCount > 0 && (
              <button
                type="button"
                onClick={handleClearFilters}
                className="btn-ghost text-xs py-1.5 px-3 rounded-lg text-rose-500 border-rose-500/30 hover:bg-rose-500/10 flex items-center gap-1 font-semibold"
              >
                <XMarkIcon className="w-3.5 h-3.5" /> Clear All Filters
              </button>
            )}
            <button
              type="button"
              onClick={handleClearFilters}
              className="btn-secondary text-xs py-1.5 px-3 rounded-lg flex items-center gap-1 font-semibold"
            >
              <ArrowPathIcon className="w-3.5 h-3.5" /> Reset Filters
            </button>
          </div>
        </div>

        {/* Multi-Select Genres Section */}
        <div className="space-y-2.5">
          <label className="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider block">
            Multi-Select Genres (Select unlimited):
          </label>
          <div className="flex flex-wrap gap-2">
            {availableGenres.map((g) => {
              const isSelected = selectedGenres.includes(g);
              return (
                <button
                  key={g}
                  type="button"
                  onClick={() => toggleGenre(g)}
                  className={`genre-pill text-xs px-3 py-1.5 rounded-full border transition-all flex items-center gap-1.5 font-medium ${
                    isSelected ? 'active shadow-md' : ''
                  }`}
                >
                  {isSelected && <CheckIcon className="w-3.5 h-3.5" />}
                  {g}
                </button>
              );
            })}
          </div>
        </div>

        {/* Additional Combined Filter Dropdowns */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
          <div>
            <label className="text-[11px] font-bold text-[var(--color-text-dim)] uppercase block mb-1">Industry / Language</label>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="input text-xs py-2 px-3 bg-[var(--color-surface-2)]"
            >
              <option value="">All Industries & Languages</option>
              <option value="te">Tollywood (Telugu)</option>
              <option value="hi">Bollywood (Hindi)</option>
              <option value="ta">Kollywood (Tamil)</option>
              <option value="ml">Mollywood (Malayalam)</option>
              <option value="kn">Sandalwood (Kannada)</option>
              <option value="en">Hollywood (English)</option>
              <option value="ko">Korean Cinema</option>
              <option value="ja">Anime / Japanese</option>
              <option value="zh">Chinese Cinema</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] font-bold text-[var(--color-text-dim)] uppercase block mb-1">Release Year</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              className="input text-xs py-2 px-3 bg-[var(--color-surface-2)]"
            >
              <option value="">All Release Years</option>
              {Array.from({ length: 35 }, (_, i) => 2026 - i).map((y) => (
                <option key={y} value={y.toString()}>{y}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[11px] font-bold text-[var(--color-text-dim)] uppercase block mb-1">Minimum Rating</label>
            <select
              value={minRating}
              onChange={(e) => setMinRating(e.target.value)}
              className="input text-xs py-2 px-3 bg-[var(--color-surface-2)]"
            >
              <option value="0">Any Star Rating</option>
              <option value="6">6.0+ Stars</option>
              <option value="7">7.0+ Stars</option>
              <option value="8">8.0+ Stars</option>
              <option value="8.5">8.5+ Top Rated</option>
            </select>
          </div>

          {!isSemantic && (
            <div>
              <label className="text-[11px] font-bold text-[var(--color-text-dim)] uppercase block mb-1">Sort Results By</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="input text-xs py-2 px-3 bg-[var(--color-surface-2)]"
              >
                <option value="popularity">Most Popular</option>
                <option value="weighted_rating">Highest Rated</option>
                <option value="release_year">Newest First</option>
              </select>
            </div>
          )}
        </div>

        {/* Selected Active Filter Badges */}
        {activeFilterCount > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[var(--color-border)]">
            <span className="text-xs font-bold text-[var(--color-text-dim)]">Selected Badges:</span>
            {selectedGenres.map((g) => (
              <span
                key={g}
                className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-[var(--color-primary)]/15 text-[var(--color-primary-light)] border border-[var(--color-primary)]/30 font-semibold"
              >
                Genre: {g}
                <button type="button" onClick={() => toggleGenre(g)} className="hover:text-red-400">
                  <XMarkIcon className="w-3.5 h-3.5" />
                </button>
              </span>
            ))}
            {selectedLanguage && (
              <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-amber-500/15 text-amber-500 dark:text-amber-400 border border-amber-500/30 font-semibold">
                Language: {selectedLanguage.toUpperCase()}
                <button type="button" onClick={() => setSelectedLanguage('')} className="hover:text-amber-300">
                  <XMarkIcon className="w-3.5 h-3.5" />
                </button>
              </span>
            )}
            {selectedYear && (
              <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30 font-semibold">
                Year: {selectedYear}
                <button type="button" onClick={() => setSelectedYear('')} className="hover:text-cyan-300">
                  <XMarkIcon className="w-3.5 h-3.5" />
                </button>
              </span>
            )}
            {minRating !== '0' && (
              <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 font-semibold">
                Min Rating: {minRating}+ Stars
                <button type="button" onClick={() => setMinRating('0')} className="hover:text-emerald-300">
                  <XMarkIcon className="w-3.5 h-3.5" />
                </button>
              </span>
            )}
          </div>
        )}
      </div>

      {/* Result Count Status Bar */}
      {total > 0 && (
        <div className="flex justify-between items-center text-xs text-[var(--color-text-muted)] px-1 font-semibold">
          <span>Found <strong className="text-[var(--color-text)] text-sm">{total.toLocaleString()}</strong> movies</span>
          <span>Showing {movies.length} of {total.toLocaleString()}</span>
        </div>
      )}

      {/* Movie Results Grid */}
      {loading ? (
        <MovieGridSkeleton count={12} />
      ) : isSemantic && semanticResults.length > 0 ? (
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-[var(--color-text)] font-['Outfit']">Semantic AI Matches</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {semanticResults.map((item) => (
              <div key={item.movie_id} className="card p-4 flex gap-4">
                <img
                  src={
                    item.poster_path
                      ? (item.poster_path.startsWith('http') ? item.poster_path : `https://image.tmdb.org/t/p/w500${item.poster_path}`)
                      : "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='150' height='225' viewBox='0 0 150 225'%3E%3Crect width='150' height='225' fill='%231a1a26'/%3E%3Ctext x='75' y='112' font-family='sans-serif' font-size='32' fill='%235a5a72' text-anchor='middle' dominant-baseline='middle'%3E🎬%3C/text%3E%3C/svg%3E"
                  }
                  alt={item.title}
                  className="w-24 aspect-[2/3] object-cover rounded-lg shrink-0"
                />
                <div className="space-y-1.5">
                  <h3 className="font-bold text-[var(--color-text)] text-lg line-clamp-1">{item.title}</h3>
                  <div className="text-xs text-[var(--color-accent)] font-bold">{item.match_percentage}% MATCH • {item.vote_average.toFixed(1)} ⭐</div>
                  <p className="text-xs text-[var(--color-text-muted)] line-clamp-3">{item.explanation}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : movies.length > 0 ? (
        <div className="space-y-8">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 sm:gap-6">
            {movies.map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>

          {/* Infinite Scroll & Load More Controls */}
          {page < totalPages && (
            <div className="flex flex-col items-center justify-center pt-8 pb-4 space-y-3">
              <button
                onClick={handleLoadMore}
                disabled={loadingMore}
                className="btn-secondary px-8 py-3 rounded-full font-bold text-sm flex items-center gap-2 shadow-xl hover:scale-105 transition-all"
              >
                {loadingMore ? (
                  <>
                    <ArrowPathIcon className="w-5 h-5 animate-spin text-[var(--color-primary)]" />
                    Loading More Movies...
                  </>
                ) : (
                  `Load More (${(total - movies.length).toLocaleString()} Remaining)`
                )}
              </button>
              <span className="text-[11px] text-[var(--color-text-dim)] font-mono">Scroll down for automatic infinite scroll</span>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-20 space-y-4 card">
          <div className="text-5xl">🎬</div>
          <h3 className="text-xl font-bold text-[var(--color-text)] font-['Outfit']">No Movies Match Your Combined Filters</h3>
          <p className="text-[var(--color-text-muted)] text-sm">Try removing a few genre filters or clearing rating restrictions.</p>
          <button onClick={handleClearFilters} className="btn-primary text-xs mt-2">Clear All Filters</button>
        </div>
      )}
    </div>
  );
};

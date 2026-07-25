import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SearchBar } from '../components/common/SearchBar';
import { MovieCard } from '../components/common/MovieCard';
import { MovieGridSkeleton } from '../components/common/Skeleton';
import { searchApi, recApi, movieApi } from '../api/client';
import type { Movie, RecommendationItem } from '../types';
import { FunnelIcon, SparklesIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

export const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [isSemantic, setIsSemantic] = useState(false);
  const [movies, setMovies] = useState<Movie[]>([]);
  const [semanticResults, setSemanticResults] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [genres, setGenres] = useState<string[]>([]);
  
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const [selectedGenre, setSelectedGenre] = useState('');
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState(searchParams.get('language') || '');
  const [minRating, setMinRating] = useState('0');
  const [sortBy, setSortBy] = useState('popularity');

  const query = searchParams.get('q') || '';

  useEffect(() => {
    movieApi.getGenres().then(setGenres).catch(console.error);
  }, []);

  useEffect(() => {
    const langFromUrl = searchParams.get('language');
    if (langFromUrl !== null && langFromUrl !== selectedLanguage) {
      setSelectedLanguage(langFromUrl);
    }
  }, [searchParams]);

  useEffect(() => {
    setPage(1);
    executeSearch(query, 1, false);
  }, [query, selectedGenre, selectedYear, selectedLanguage, minRating, sortBy, isSemantic]);

  const executeSearch = async (searchQuery: string, pageNum: number, append: boolean) => {
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

    try {
      if (isSemantic && searchQuery.trim()) {
        const res = await recApi.postSemanticSearch(searchQuery, 20);
        setSemanticResults(res.recommendations);
        setMovies([]);
        setTotal(res.total);
        setTotalPages(1);
      } else {
        const params: any = {
          page: pageNum,
          per_page: 20,
          sort: sortBy,
          min_rating: parseFloat(minRating),
        };
        if (selectedGenre) params.genre = selectedGenre;
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

  const handleSearchSubmit = (newQuery: string) => {
    setSearchParams({ q: newQuery });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="space-y-4 max-w-3xl mx-auto text-center">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white font-['Outfit']">
          Search & Discover
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
                : 'bg-[var(--color-surface-2)] border-[var(--color-border)] text-gray-400 hover:text-white'
            }`}
          >
            <SparklesIcon className="w-4 h-4" />
            {isSemantic ? 'Semantic Natural Language Search ON' : 'Switch to Semantic AI Search'}
          </button>
        </div>
      </div>

      <div className="card p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-300">
          <FunnelIcon className="w-5 h-5 text-[var(--color-primary-light)]" />
          Filters:
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedGenre}
            onChange={(e) => setSelectedGenre(e.target.value)}
            className="input text-xs py-2 px-3 w-auto bg-[var(--color-surface-2)]"
          >
            <option value="">All Genres</option>
            {genres.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>

          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="input text-xs py-2 px-3 w-auto bg-[var(--color-surface-2)]"
          >
            <option value="">All Languages / Industries</option>
            <option value="en">Hollywood (English)</option>
            <option value="hi">Bollywood (Hindi)</option>
            <option value="te">Tollywood (Telugu)</option>
            <option value="ta">Kollywood (Tamil)</option>
            <option value="ml">Mollywood (Malayalam)</option>
            <option value="kn">Sandalwood (Kannada)</option>
            <option value="ko">Korean Cinema</option>
            <option value="ja">Anime / Japanese</option>
            <option value="zh">Chinese Cinema</option>
            <option value="es">Spanish Cinema</option>
            <option value="fr">French Cinema</option>
          </select>

          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            className="input text-xs py-2 px-3 w-auto bg-[var(--color-surface-2)]"
          >
            <option value="">All Years</option>
            {Array.from({ length: 30 }, (_, i) => 2026 - i).map((y) => (
              <option key={y} value={y.toString()}>{y}</option>
            ))}
          </select>

          <select
            value={minRating}
            onChange={(e) => setMinRating(e.target.value)}
            className="input text-xs py-2 px-3 w-auto bg-[var(--color-surface-2)]"
          >
            <option value="0">Min Rating: Any</option>
            <option value="7">7.0+ Stars</option>
            <option value="8">8.0+ Stars</option>
          </select>

          {!isSemantic && (
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="input text-xs py-2 px-3 w-auto bg-[var(--color-surface-2)]"
            >
              <option value="popularity">Most Popular</option>
              <option value="weighted_rating">Top Rated</option>
              <option value="release_year">Newest First</option>
            </select>
          )}

          <button
            type="button"
            onClick={() => {
              setSelectedGenre('');
              setSelectedYear('');
              setSelectedLanguage('');
              setMinRating('0');
              setSortBy('popularity');
            }}
            className="flex items-center gap-1 text-xs font-semibold text-gray-400 hover:text-white transition-colors py-2 px-3 rounded-lg bg-[var(--color-surface-2)] border border-[var(--color-border)]"
          >
            <ArrowPathIcon className="w-3.5 h-3.5" /> Clear Filters
          </button>
        </div>
      </div>

      {total > 0 && (
        <div className="flex justify-between items-center text-xs text-gray-400 px-1 font-semibold">
          <span>Found <strong className="text-white">{total.toLocaleString()}</strong> movies</span>
          <span>Showing {movies.length} of {total.toLocaleString()}</span>
        </div>
      )}

      {loading ? (
        <MovieGridSkeleton count={10} />
      ) : isSemantic && semanticResults.length > 0 ? (
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-white font-['Outfit']">Semantic AI Matches</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {semanticResults.map((item) => (
              <div key={item.movie_id} className="card p-4 flex gap-4">
                <img
                  src={
                    item.poster_path
                      ? `https://image.tmdb.org/t/p/w500${item.poster_path}`
                      : "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='150' height='225' viewBox='0 0 150 225'%3E%3Crect width='150' height='225' fill='%231a1a26'/%3E%3Ctext x='75' y='112' font-family='sans-serif' font-size='32' fill='%235a5a72' text-anchor='middle' dominant-baseline='middle'%3E🎬%3C/text%3E%3C/svg%3E"
                  }
                  alt={item.title}
                  className="w-24 aspect-[2/3] object-cover rounded-lg"
                />
                <div>
                  <h3 className="font-bold text-white text-lg">{item.title}</h3>
                  <div className="text-xs text-[var(--color-accent)] font-semibold mt-1">Match: {item.match_percentage}%</div>
                  <p className="text-xs text-gray-400 mt-2 line-clamp-3">{item.explanation}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : movies.length > 0 ? (
        <div className="space-y-8">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
            {movies.map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>

          {page < totalPages && (
            <div className="flex justify-center pt-6">
              <button
                onClick={handleLoadMore}
                disabled={loadingMore}
                className="btn-secondary px-8 py-3 rounded-full font-bold text-sm flex items-center gap-2 shadow-xl hover:scale-105 transition-all"
              >
                {loadingMore ? (
                  <>
                    <ArrowPathIcon className="w-5 h-5 animate-spin" />
                    Loading More Movies...
                  </>
                ) : (
                  `Load More (${total - movies.length} Remaining)`
                )}
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-20 space-y-4">
          <div className="text-5xl">🎬</div>
          <h3 className="text-xl font-bold text-white font-['Outfit']">No Movies Found</h3>
          <p className="text-gray-400 text-sm">Try adjusting your query or filter parameters.</p>
        </div>
      )}
    </div>
  );
};

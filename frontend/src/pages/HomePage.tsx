import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { SparklesIcon, FireIcon, TrophyIcon, CalendarIcon, PlayIcon, ArrowPathIcon } from '@heroicons/react/24/solid';
import { movieApi } from '../api/client';
import type { Movie } from '../types';
import { MovieCard } from '../components/common/MovieCard';
import { MovieGridSkeleton } from '../components/common/Skeleton';
import { SearchBar } from '../components/common/SearchBar';
import { useMovieStore } from '../store/movieStore';

const MOODS = [
  { id: 'happy', label: '😊 Feel-Good & Happy', color: 'from-amber-500/20 to-yellow-500/20' },
  { id: 'action', label: '⚡ High Octane Action', color: 'from-red-500/20 to-orange-500/20' },
  { id: 'scifi', label: '🚀 Mind-Bending Sci-Fi', color: 'from-cyan-500/20 to-blue-500/20' },
  { id: 'romantic', label: '❤️ Romantic & Emotional', color: 'from-pink-500/20 to-rose-500/20' },
  { id: 'crime', label: '🕵️ Crime & Mystery', color: 'from-purple-500/20 to-indigo-500/20' },
  { id: 'horror', label: '👻 Spooky & Horror', color: 'from-emerald-500/20 to-teal-500/20' },
];

export const HomePage: React.FC = () => {
  const [trending, setTrending] = useState<Movie[]>([]);
  const [topRated, setTopRated] = useState<Movie[]>([]);
  const [popular, setPopular] = useState<Movie[]>([]);
  const [exploreMovies, setExploreMovies] = useState<Movie[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [heroMovie, setHeroMovie] = useState<Movie | null>(null);

  const navigate = useNavigate();
  const { openTrailer } = useMovieStore();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [tr, top, pop, initialExplore] = await Promise.all([
          movieApi.getTrending(10),
          movieApi.getTopRated(10),
          movieApi.getPopular(10),
          movieApi.getMovies({ page: 1, per_page: 20 }),
        ]);
        setTrending(tr);
        setTopRated(top);
        setPopular(pop);
        if (initialExplore && initialExplore.items) {
          setExploreMovies(initialExplore.items);
          setHasMore(initialExplore.page < initialExplore.pages);
        }
        if (tr.length > 0) {
          setHeroMovie(tr[0]);
        }
      } catch (err) {
        console.error('Failed to fetch home page data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const loadMoreMovies = async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const nextPage = page + 1;
      const res = await movieApi.getMovies({ page: nextPage, per_page: 20 });
      if (res && res.items.length > 0) {
        setExploreMovies((prev) => {
          const existingIds = new Set(prev.map((m) => m.id));
          const newItems = res.items.filter((m) => !existingIds.has(m.id));
          return [...prev, ...newItems];
        });
        setPage(nextPage);
        setHasMore(res.page < res.pages);
      } else {
        setHasMore(false);
      }
    } catch (err) {
      console.error('Failed to load more movies', err);
    } finally {
      setLoadingMore(false);
    }
  };

  const heroBackdrop = heroMovie?.backdrop_path
    ? (heroMovie.backdrop_path.startsWith('http') ? heroMovie.backdrop_path : `https://image.tmdb.org/t/p/original${heroMovie.backdrop_path}`)
    : 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=1920&q=80';

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <div className="relative min-h-[80vh] flex items-center justify-center overflow-hidden rounded-3xl mx-4 sm:mx-8 border border-[var(--color-border)] shadow-2xl mt-4">
        <div className="absolute inset-0 z-0">
          <img src={heroBackdrop} alt="Hero Backdrop" className="w-full h-full object-cover filter brightness-[0.4] scale-105 transition-transform duration-1000" />
          <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-bg)] via-[var(--color-bg)]/60 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--color-bg)] via-[var(--color-bg)]/40 to-transparent" />
        </div>

        <div className="relative z-10 max-w-5xl mx-auto px-6 py-20 text-center space-y-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-amber-500/30 text-amber-300 text-xs sm:text-sm font-semibold tracking-wide uppercase">
            <SparklesIcon className="w-4 h-4 text-amber-400 animate-spin" />
            Next-Gen Hybrid Recommendation Engine
          </div>

          <h1 className="text-4xl sm:text-6xl md:text-7xl font-black tracking-tight font-['Outfit'] text-white leading-none">
            Find Your Next Favorite <span className="gradient-text">Movie With AI</span>
          </h1>

          <p className="max-w-2xl mx-auto text-base sm:text-xl text-gray-300 font-normal leading-relaxed">
            Discover films tailored to your mood, taste profile, and natural language prompts using TF-IDF, Cosine Similarity & Sentence Transformers.
          </p>

          <div className="max-w-2xl mx-auto pt-2">
            <SearchBar placeholder='Try searching "Tollywood", "Bollywood", "Marvel", "Inception"...' />
          </div>

          {heroMovie && (
            <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
              <Link to={`/movies/${heroMovie.id}`} className="btn-primary">
                Explore Featured: {heroMovie.title}
              </Link>
              {heroMovie.trailer_key && (
                <button
                  onClick={() => openTrailer(heroMovie.trailer_key!, heroMovie.title)}
                  className="btn-ghost"
                >
                  <PlayIcon className="w-5 h-5 text-[var(--color-primary-light)]" />
                  Watch Trailer
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Mood Selector */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex items-center gap-3">
          <SparklesIcon className="w-6 h-6 text-[var(--color-accent)]" />
          <h2 className="section-title mb-0">What's Your Vibe Today?</h2>
        </div>
        <p className="text-gray-400 text-sm">Select your current mood to get instant tailored recommendations.</p>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {MOODS.map((m) => (
            <button
              key={m.id}
              onClick={() => navigate(`/recommendations?mood=${m.id}`)}
              className={`p-4 rounded-2xl bg-gradient-to-br ${m.color} border border-[var(--color-border)] hover:border-[var(--color-accent)] text-left transition-all hover:-translate-y-1 group`}
            >
              <div className="text-sm font-bold text-white group-hover:text-[var(--color-accent)] transition-colors">
                {m.label}
              </div>
              <span className="text-[11px] text-gray-400 mt-2 block">AI Match &rarr;</span>
            </button>
          ))}
        </div>
      </section>

      {/* Trending Movies */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FireIcon className="w-6 h-6 text-red-500" />
            <h2 className="section-title mb-0">Trending Right Now</h2>
          </div>
          <Link to="/search?sort=popularity" className="text-xs font-semibold text-[var(--color-primary-light)] hover:underline">
            View All &rarr;
          </Link>
        </div>

        {loading ? (
          <MovieGridSkeleton count={5} />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
            {trending.map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
        )}
      </section>

      {/* Top Rated Masterpieces */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <TrophyIcon className="w-6 h-6 text-[var(--color-accent)]" />
            <h2 className="section-title mb-0">Top Rated Masterpieces</h2>
          </div>
          <Link to="/search?sort=weighted_rating" className="text-xs font-semibold text-[var(--color-accent)] hover:underline">
            View All &rarr;
          </Link>
        </div>

        {loading ? (
          <MovieGridSkeleton count={5} />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
            {topRated.map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
        )}
      </section>

      {/* Regional Cinema */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex items-center gap-3">
          <CalendarIcon className="w-6 h-6 text-blue-400" />
          <h2 className="section-title mb-0">Explore Regional & World Cinema</h2>
        </div>
        <p className="text-gray-400 text-sm">Browse movies across Hollywood, Indian Cinema (Bollywood, Tollywood, Kollywood, Mollywood, Sandalwood), Korean, and Anime.</p>

        <div className="flex flex-wrap gap-2 pt-2">
          {[
            { name: '🌟 Hollywood', query: 'Hollywood' },
            { name: '💃 Bollywood (Hindi)', query: 'Bollywood' },
            { name: '🔥 Tollywood (Telugu)', query: 'Tollywood' },
            { name: '🎬 Kollywood (Tamil)', query: 'Kollywood' },
            { name: '🌴 Mollywood (Malayalam)', query: 'Mollywood' },
            { name: '👑 Sandalwood (Kannada)', query: 'Sandalwood' },
            { name: '🍿 K-Drama & Korean', lang: 'ko' },
            { name: '⛩️ Anime & Japanese', query: 'Anime' },
            { name: '🐉 Chinese Cinema', lang: 'zh' },
            { name: '🇫🇷 French Cinema', lang: 'fr' },
            { name: '🇪🇸 Spanish Cinema', lang: 'es' },
            { name: '🇮🇹 Italian Cinema', lang: 'it' },
            { name: '🇩🇪 German Cinema', lang: 'de' },
          ].map((ind) => (
            <Link
              key={ind.name}
              to={ind.query ? `/search?q=${encodeURIComponent(ind.query)}` : `/search?language=${ind.lang}`}
              className="px-4 py-2.5 rounded-xl glass border border-[var(--color-border)] hover:border-[var(--color-primary-light)] text-xs sm:text-sm font-semibold text-gray-200 hover:text-white transition-all hover:-translate-y-0.5"
            >
              {ind.name}
            </Link>
          ))}
        </div>
      </section>

      {/* Popular Movies */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CalendarIcon className="w-6 h-6 text-purple-400" />
            <h2 className="section-title mb-0">Popular Movies</h2>
          </div>
          <Link to="/search?sort=popularity" className="text-xs font-semibold text-[var(--color-primary-light)] hover:underline">
            View All &rarr;
          </Link>
        </div>

        {loading ? (
          <MovieGridSkeleton count={5} />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
            {popular.map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
        )}
      </section>

      {/* Full Movie Catalog — Paginated Endless Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6 pt-8 border-t border-[var(--color-border)]">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="section-title mb-1">Explore Full Movie Catalog</h2>
            <p className="text-gray-400 text-sm">Discover all 20,000+ movies in our database</p>
          </div>
          <span className="text-xs font-semibold px-3 py-1 rounded-full bg-[var(--color-surface-2)] text-gray-300 border border-[var(--color-border)]">
            Page {page}
          </span>
        </div>

        {loading ? (
          <MovieGridSkeleton count={10} />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
            {exploreMovies.map((movie) => (
              <MovieCard key={`explore-${movie.id}`} movie={movie} />
            ))}
          </div>
        )}

        {hasMore && (
          <div className="text-center pt-8">
            <button
              onClick={loadMoreMovies}
              disabled={loadingMore}
              className="btn-secondary px-8 py-3 text-sm font-bold shadow-lg"
            >
              {loadingMore ? (
                <>
                  <ArrowPathIcon className="w-4 h-4 animate-spin text-[var(--color-accent)]" /> Loading More Movies...
                </>
              ) : (
                'Load More Movies 👇'
              )}
            </button>
          </div>
        )}
      </section>
    </div>
  );
};

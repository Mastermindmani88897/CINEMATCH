import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { SparklesIcon, FireIcon, TrophyIcon, CalendarIcon, PlayIcon } from '@heroicons/react/24/solid';
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
  const [loading, setLoading] = useState(true);
  const [heroMovie, setHeroMovie] = useState<Movie | null>(null);

  const navigate = useNavigate();
  const { openTrailer } = useMovieStore();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [tr, top, pop] = await Promise.all([
          movieApi.getTrending(10),
          movieApi.getTopRated(10),
          movieApi.getPopular(10),
        ]);
        setTrending(tr);
        setTopRated(top);
        setPopular(pop);
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

  const heroBackdrop = heroMovie?.backdrop_path
    ? (heroMovie.backdrop_path.startsWith('http') ? heroMovie.backdrop_path : `https://image.tmdb.org/t/p/original${heroMovie.backdrop_path}`)
    : 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=1920&q=80';

  return (
    <div className="space-y-16 pb-16">
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
            <SearchBar placeholder='Try searching "emotional space survival movies" or "Inception"...' />
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
            {trending.slice(0, 5).map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
        )}
      </section>

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
            {topRated.slice(0, 5).map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
        )}
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex items-center gap-3">
          <CalendarIcon className="w-6 h-6 text-blue-400" />
          <h2 className="section-title mb-0">Popular Movies</h2>
        </div>

        {loading ? (
          <MovieGridSkeleton count={5} />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
            {popular.slice(0, 5).map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

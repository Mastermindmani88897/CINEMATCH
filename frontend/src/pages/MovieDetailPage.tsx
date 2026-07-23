import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { StarIcon, PlayIcon, HeartIcon, BookmarkIcon, SparklesIcon, AdjustmentsHorizontalIcon, PencilSquareIcon } from '@heroicons/react/24/solid';
import { HeartIcon as HeartOutline, BookmarkIcon as BookmarkOutline } from '@heroicons/react/24/outline';
import { movieApi, recApi, userApi } from '../api/client';
import type { Movie, RecommendationItem, ReviewResponse, NoteResponse } from '../types';
import { MovieCard } from '../components/common/MovieCard';
import { RatingWidget } from '../components/common/RatingWidget';
import { useMovieStore } from '../store/movieStore';
import { useAuthStore } from '../store/authStore';
import toast from 'react-hot-toast';

export const MovieDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const movieId = parseInt(id || '0');

  const [movie, setMovie] = useState<Movie | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [reviews, setReviews] = useState<ReviewResponse[]>([]);
  const [userNote, setUserNote] = useState('');
  const [userRating, setUserRating] = useState(0);
  const [newReview, setNewReview] = useState('');
  const [loading, setLoading] = useState(true);

  const { openTrailer, favoriteIds, watchlistIds, toggleFavoriteId, toggleWatchlistId } = useMovieStore();
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  const isFav = favoriteIds.includes(movieId);
  const isWatch = watchlistIds.includes(movieId);

  useEffect(() => {
    if (!movieId) return;
    const fetchMovieData = async () => {
      setLoading(true);
      try {
        const data = await movieApi.getMovieById(movieId);
        setMovie(data);

        recApi.getContentRecs(movieId, 10).then((r) => setRecommendations(r.recommendations)).catch(() => {});
        userApi.getReviews(movieId).then(setReviews).catch(() => {});

        if (isAuthenticated) {
          userApi.getNote(movieId).then((n: NoteResponse | null) => n && setUserNote(n.content)).catch(() => {});
          userApi.logHistory(movieId).catch(() => {});
        }
      } catch (err) {
        console.error('Failed to load movie', err);
      } finally {
        setLoading(false);
      }
    };
    fetchMovieData();
  }, [movieId, isAuthenticated]);

  if (loading || !movie) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <div className="skeleton h-96 w-full rounded-3xl" />
      </div>
    );
  }

  const posterUrl = movie.poster_path
    ? (movie.poster_path.startsWith('http') ? movie.poster_path : `https://image.tmdb.org/t/p/w500${movie.poster_path}`)
    : 'https://via.placeholder.com/500x750?text=No+Poster';

  const backdropUrl = movie.backdrop_path
    ? (movie.backdrop_path.startsWith('http') ? movie.backdrop_path : `https://image.tmdb.org/t/p/original${movie.backdrop_path}`)
    : posterUrl;

  const handleFavorite = async () => {
    if (!isAuthenticated) return toast.error('Sign in required');
    toggleFavoriteId(movieId);
    try {
      if (isFav) await userApi.removeFavorite(movieId);
      else await userApi.addFavorite(movieId);
    } catch {
      toggleFavoriteId(movieId);
    }
  };

  const handleWatchlist = async () => {
    if (!isAuthenticated) return toast.error('Sign in required');
    toggleWatchlistId(movieId);
    try {
      if (isWatch) await userApi.removeWatchlist(movieId);
      else await userApi.addWatchlist(movieId);
    } catch {
      toggleWatchlistId(movieId);
    }
  };

  const handleRate = async (rating: number) => {
    if (!isAuthenticated) return toast.error('Sign in required');
    setUserRating(rating);
    try {
      await userApi.rateMovie(movieId, rating);
      toast.success(`Rated ${rating} stars!`);
    } catch {
      toast.error('Failed to save rating');
    }
  };

  const handleSaveNote = async () => {
    if (!isAuthenticated) return toast.error('Sign in required');
    try {
      await userApi.saveNote(movieId, userNote);
      toast.success('Personal note saved');
    } catch {
      toast.error('Failed to save note');
    }
  };

  const handleAddReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAuthenticated) return toast.error('Sign in required');
    if (!newReview.trim()) return;
    try {
      const created = await userApi.createReview(movieId, newReview);
      setReviews([created, ...reviews]);
      setNewReview('');
      toast.success('Review posted');
    } catch {
      toast.error('Failed to post review');
    }
  };

  return (
    <div className="space-y-12 pb-16">
      <div className="relative min-h-[60vh] flex items-end overflow-hidden border-b border-[var(--color-border)]">
        <img src={backdropUrl} alt={movie.title} className="absolute inset-0 w-full h-full object-cover filter brightness-[0.3]" />
        <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-bg)] via-[var(--color-bg)]/70 to-transparent" />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 w-full flex flex-col md:flex-row gap-8 items-end">
          <img src={posterUrl} alt={movie.title} className="w-48 sm:w-64 aspect-[2/3] object-cover rounded-2xl shadow-2xl border border-white/10 shrink-0" />

          <div className="space-y-4 flex-1">
            <div className="flex flex-wrap items-center gap-3 text-xs text-gray-300">
              <span className="px-2.5 py-1 rounded-md bg-white/10 font-bold text-[var(--color-accent)] flex items-center gap-1">
                <StarIcon className="w-4 h-4" /> {movie.vote_average.toFixed(1)} ({movie.vote_count} votes)
              </span>
              <span>{movie.release_year}</span>
              {movie.runtime && <span>• {movie.runtime} min</span>}
              {movie.original_language && <span className="uppercase">• {movie.original_language}</span>}
            </div>

            <h1 className="text-3xl sm:text-5xl font-black text-white font-['Outfit']">{movie.title}</h1>
            {movie.tagline && <p className="italic text-gray-400 text-sm sm:text-base">"{movie.tagline}"</p>}

            <div className="flex flex-wrap gap-2 pt-1">
              {movie.genres?.map((g) => (
                <span key={g} className="genre-pill">{g}</span>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-4 pt-4">
              {movie.trailer_key && (
                <button onClick={() => openTrailer(movie.trailer_key!, movie.title)} className="btn-primary">
                  <PlayIcon className="w-5 h-5" /> Watch Trailer
                </button>
              )}
              <button onClick={handleFavorite} className={`btn-ghost ${isFav ? 'text-red-500 border-red-500' : ''}`}>
                {isFav ? <HeartIcon className="w-5 h-5" /> : <HeartOutline className="w-5 h-5" />} Favorite
              </button>
              <button onClick={handleWatchlist} className={`btn-ghost ${isWatch ? 'text-[var(--color-accent)] border-[var(--color-accent)]' : ''}`}>
                {isWatch ? <BookmarkIcon className="w-5 h-5" /> : <BookmarkOutline className="w-5 h-5" />} Watchlist
              </button>
              <button onClick={() => navigate(`/compare?m1=${movie.id}`)} className="btn-ghost" title="Compare with another movie">
                <AdjustmentsHorizontalIcon className="w-5 h-5" /> Compare
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-3 gap-12">
        <div className="lg:col-span-2 space-y-10">
          <section className="space-y-3">
            <h2 className="text-2xl font-bold text-white font-['Outfit']">Overview</h2>
            <p className="text-gray-300 leading-relaxed text-base">{movie.overview || 'No overview available.'}</p>
          </section>

          {movie.cast && movie.cast.length > 0 && (
            <section className="space-y-4">
              <h2 className="text-2xl font-bold text-white font-['Outfit']">Top Cast</h2>
              <div className="carousel-scroll">
                {movie.cast.slice(0, 10).map((c, i) => (
                  <div key={i} className="w-32 card p-3 text-center shrink-0 space-y-2">
                    <div className="w-20 h-20 mx-auto rounded-full bg-[var(--color-surface-2)] overflow-hidden flex items-center justify-center font-bold text-xl text-gray-400">
                      {c.name.charAt(0)}
                    </div>
                    <div className="font-semibold text-xs text-white line-clamp-1">{c.name}</div>
                    <div className="text-[11px] text-gray-400 line-clamp-1">{c.character}</div>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className="space-y-6">
            <h2 className="text-2xl font-bold text-white font-['Outfit']">Reviews</h2>
            {isAuthenticated && (
              <form onSubmit={handleAddReview} className="card p-4 space-y-3">
                <textarea
                  value={newReview}
                  onChange={(e) => setNewReview(e.target.value)}
                  placeholder="Write your review or thoughts on this movie..."
                  className="input min-h-[100px] text-sm"
                />
                <button type="submit" className="btn-primary text-xs py-2 px-4">Post Review</button>
              </form>
            )}

            <div className="space-y-4">
              {reviews.length > 0 ? (
                reviews.map((r) => (
                  <div key={r.id} className="card p-4 space-y-2">
                    <div className="flex justify-between items-center text-xs text-gray-400">
                      <span className="font-semibold text-gray-200">User #{r.user_id}</span>
                      <span>{new Date(r.created_at).toLocaleDateString()}</span>
                    </div>
                    <p className="text-sm text-gray-300 leading-relaxed">{r.content}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">No reviews yet. Be the first to leave one!</p>
              )}
            </div>
          </section>
        </div>

        <div className="space-y-8">
          <div className="card p-6 space-y-4 border-[var(--color-primary)]/30">
            <h3 className="font-bold text-white text-lg font-['Outfit'] flex items-center gap-2">
              <PencilSquareIcon className="w-5 h-5 text-[var(--color-accent)]" /> Your Interactive Rating
            </h3>
            <RatingWidget initialRating={userRating} onRate={handleRate} disabled={!isAuthenticated} />

            <div className="pt-4 border-t border-[var(--color-border)] space-y-2">
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Personal Movie Notes</label>
              <textarea
                value={userNote}
                onChange={(e) => setUserNote(e.target.value)}
                placeholder="Add private notes (e.g. 'Watched with Alex')..."
                className="input text-xs min-h-[80px]"
                disabled={!isAuthenticated}
              />
              {isAuthenticated && (
                <button onClick={handleSaveNote} className="btn-ghost text-xs w-full py-2">Save Note</button>
              )}
            </div>
          </div>

          <div className="card p-6 space-y-3 text-sm">
            <h3 className="font-bold text-white font-['Outfit'] mb-2">Movie Metadata</h3>
            <div className="flex justify-between text-gray-400 py-1 border-b border-white/5">
              <span>Director:</span> <span className="text-white font-medium">{movie.director || 'N/A'}</span>
            </div>
            <div className="flex justify-between text-gray-400 py-1 border-b border-white/5">
              <span>Weighted Rating:</span> <span className="text-[var(--color-accent)] font-bold">{movie.weighted_rating?.toFixed(2) || 'N/A'}</span>
            </div>
            <div className="flex justify-between text-gray-400 py-1 border-b border-white/5">
              <span>Popularity Score:</span> <span className="text-white font-medium">{movie.popularity?.toFixed(1)}</span>
            </div>
          </div>
        </div>
      </div>

      {recommendations.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6 pt-8 border-t border-[var(--color-border)]">
          <div className="flex items-center gap-3">
            <SparklesIcon className="w-6 h-6 text-[var(--color-accent)]" />
            <h2 className="section-title mb-0">AI Content-Based Similar Movies</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
            {recommendations.slice(0, 5).map((rec) => (
              <MovieCard
                key={rec.movie_id}
                movie={{
                  id: rec.movie_id,
                  title: rec.title,
                  poster_path: rec.poster_path,
                  vote_average: rec.vote_average,
                  release_year: rec.release_year,
                  vote_count: 0,
                  popularity: 0,
                  genres: rec.genres,
                }}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

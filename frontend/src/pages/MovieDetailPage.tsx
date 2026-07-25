import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  StarIcon, PlayIcon, HeartIcon, BookmarkIcon, SparklesIcon,
  AdjustmentsHorizontalIcon, PencilSquareIcon, TrashIcon, ChevronDownIcon, ChevronUpIcon
} from '@heroicons/react/24/solid';
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
  const [editingReviewId, setEditingReviewId] = useState<number | null>(null);
  const [editReviewContent, setEditReviewContent] = useState('');
  const [showFullCrew, setShowFullCrew] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  const { openTrailer, favoriteIds, watchlistIds, toggleFavoriteId, toggleWatchlistId } = useMovieStore();
  const { user, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  const isFav = favoriteIds.includes(movieId);
  const isWatch = watchlistIds.includes(movieId);

  useEffect(() => {
    if (!movieId) return;
    const fetchMovieData = async () => {
      setLoading(true);
      setIsError(false);
      try {
        const data = await movieApi.getMovieById(movieId);
        setMovie(data);

        if (data.genres && data.genres.length > 0) {
          recApi.getGenreRecs(data.genres[0], 10).then((r) => setRecommendations(r.recommendations)).catch(() => {});
        } else {
          recApi.getPopularRecs('weighted', 10).then((r) => setRecommendations(r.recommendations)).catch(() => {});
        }
        userApi.getReviews(movieId).then(setReviews).catch(() => {});

        if (isAuthenticated) {
          userApi.getNote(movieId).then((n: NoteResponse | null) => n && setUserNote(n.content)).catch(() => {});
          userApi.logHistory(movieId).catch(() => {});
        }
      } catch (err) {
        console.error('Failed to load movie', err);
        setIsError(true);
      } finally {
        setLoading(false);
      }
    };
    fetchMovieData();
  }, [movieId, isAuthenticated]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center space-y-4">
        <div className="skeleton h-[60vh] w-full rounded-3xl" />
      </div>
    );
  }

  if (isError || !movie) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center space-y-6">
        <div className="text-6xl">🎬</div>
        <h1 className="text-3xl font-black text-[var(--color-text)] font-['Outfit']">Movie Not Found</h1>
        <p className="text-[var(--color-text-muted)]">The movie you're looking for doesn't exist or was removed.</p>
        <button onClick={() => navigate(-1)} className="btn-primary">← Go Back</button>
      </div>
    );
  }

  const POSTER_FALLBACK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='500' height='750' viewBox='0 0 500 750'%3E%3Crect width='500' height='750' fill='%231a1a26'/%3E%3Ctext x='250' y='375' font-family='Inter,sans-serif' font-size='24' fill='%235a5a72' text-anchor='middle' dominant-baseline='middle'%3E🎬 No Poster%3C/text%3E%3C/svg%3E";

  const posterUrl = movie.poster_path
    ? (movie.poster_path.startsWith('http') ? movie.poster_path : `https://image.tmdb.org/t/p/w500${movie.poster_path}`)
    : POSTER_FALLBACK;

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

  const handleUpdateReview = async (reviewId: number) => {
    if (!editReviewContent.trim()) return;
    try {
      const updated = await userApi.updateReview(reviewId, editReviewContent);
      setReviews((prev) => prev.map((r) => (r.id === reviewId ? updated : r)));
      setEditingReviewId(null);
      toast.success('Review updated');
    } catch {
      toast.error('Failed to update review');
    }
  };

  const handleDeleteReview = async (reviewId: number) => {
    if (!window.confirm('Are you sure you want to delete your review?')) return;
    try {
      await userApi.deleteReview(reviewId);
      setReviews((prev) => prev.filter((r) => r.id !== reviewId));
      toast.success('Review deleted');
    } catch {
      toast.error('Failed to delete review');
    }
  };

  // Format currency
  const formatCurrency = (amount?: number) => {
    if (!amount || amount === 0) return 'N/A';
    return `$${amount.toLocaleString()}`;
  };

  return (
    <div className="space-y-12 pb-16">
      {/* Hero Header */}
      <div className="relative min-h-[60vh] flex items-end overflow-hidden border-b border-[var(--color-border)]">
        <img src={backdropUrl} alt={movie.title} className="absolute inset-0 w-full h-full object-cover filter brightness-[0.3]" />
        <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-bg)] via-[var(--color-bg)]/75 to-transparent" />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 w-full flex flex-col md:flex-row gap-8 items-end">
          <img src={posterUrl} alt={movie.title} className="w-48 sm:w-64 aspect-[2/3] object-cover rounded-2xl shadow-2xl border border-white/10 shrink-0" />

          <div className="space-y-4 flex-1">
            <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--color-text-muted)]">
              <span className="px-2.5 py-1 rounded-md bg-[var(--color-surface)] font-bold text-[var(--color-accent)] border border-[var(--color-border)] flex items-center gap-1">
                <StarIcon className="w-4 h-4" /> {movie.vote_average.toFixed(1)} ({movie.vote_count.toLocaleString()} votes)
              </span>
              <span className="font-semibold text-[var(--color-text)]">{movie.release_year}</span>
              {movie.runtime && <span>• {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m ({movie.runtime} min)</span>}
              {movie.original_language && <span className="uppercase font-bold text-[var(--color-primary-light)]">• {movie.original_language}</span>}
              {movie.certification && <span className="px-2 py-0.5 rounded border border-[var(--color-border)] font-bold">{movie.certification}</span>}
            </div>

            <h1 className="text-3xl sm:text-5xl font-black text-[var(--color-text)] font-['Outfit']">{movie.title}</h1>
            {movie.tagline && <p className="italic text-[var(--color-text-muted)] text-sm sm:text-base">"{movie.tagline}"</p>}

            <div className="flex flex-wrap gap-2 pt-1">
              {movie.genres?.map((g) => (
                <span key={g} className="genre-pill">{g}</span>
              ))}
            </div>

            {/* Action Bar */}
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
                <AdjustmentsHorizontalIcon className="w-5 h-5" /> Compare Side-by-Side
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-3 gap-12">
        <div className="lg:col-span-2 space-y-10">
          {/* Overview */}
          <section className="space-y-3">
            <h2 className="text-2xl font-bold text-[var(--color-text)] font-['Outfit']">Story & Overview</h2>
            <p className="text-[var(--color-text-muted)] leading-relaxed text-base">{movie.overview || 'No overview available.'}</p>
          </section>

          {/* Top Cast Section */}
          {movie.cast && movie.cast.length > 0 && (
            <section className="space-y-4">
              <h2 className="text-2xl font-bold text-[var(--color-text)] font-['Outfit']">Top Cast</h2>
              <div className="carousel-scroll">
                {movie.cast.slice(0, 15).map((c, i) => {
                  const castPhoto = c.profile_path
                    ? (c.profile_path.startsWith('http') ? c.profile_path : `https://image.tmdb.org/t/p/w185${c.profile_path}`)
                    : null;

                  return (
                    <div key={i} className="w-32 card p-3 text-center shrink-0 space-y-2 group hover:border-[var(--color-primary)] transition-all">
                      {castPhoto ? (
                        <img src={castPhoto} alt={c.name} className="w-20 h-20 mx-auto rounded-full object-cover shadow-md group-hover:scale-105 transition-transform" />
                      ) : (
                        <div className="w-20 h-20 mx-auto rounded-full bg-[var(--color-surface-2)] overflow-hidden flex items-center justify-center font-bold text-xl text-[var(--color-text-dim)] border border-[var(--color-border)]">
                          {c.name.charAt(0)}
                        </div>
                      )}
                      <div className="font-bold text-xs text-[var(--color-text)] line-clamp-1">{c.name}</div>
                      <div className="text-[11px] text-[var(--color-text-muted)] line-clamp-1">{c.character || 'Role N/A'}</div>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* Crew Section */}
          {movie.crew && movie.crew.length > 0 && (
            <section className="space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-[var(--color-text)] font-['Outfit']">Key Crew & Production Team</h2>
                <button
                  type="button"
                  onClick={() => setShowFullCrew(!showFullCrew)}
                  className="btn-ghost text-xs py-1.5 px-3 rounded-lg flex items-center gap-1.5 font-semibold"
                >
                  {showFullCrew ? <ChevronUpIcon className="w-4 h-4" /> : <ChevronDownIcon className="w-4 h-4" />}
                  {showFullCrew ? 'Show Less Crew' : `Show All Crew (${movie.crew.length})`}
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {(showFullCrew ? movie.crew : movie.crew.slice(0, 8)).map((cr, idx) => (
                  <div key={idx} className="card p-3 space-y-1">
                    <div className="font-bold text-xs text-[var(--color-text)] line-clamp-1">{cr.name}</div>
                    <div className="text-[11px] text-[var(--color-primary-light)] font-semibold">{cr.job}</div>
                    {cr.department && <div className="text-[10px] text-[var(--color-text-dim)] uppercase">{cr.department}</div>}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Reviews Section */}
          <section className="space-y-6">
            <h2 className="text-2xl font-bold text-[var(--color-text)] font-['Outfit']">User Reviews ({reviews.length})</h2>

            {isAuthenticated && (
              <form onSubmit={handleAddReview} className="card p-4 space-y-3">
                <textarea
                  value={newReview}
                  onChange={(e) => setNewReview(e.target.value)}
                  placeholder="Share your thoughts or review on this movie..."
                  className="input min-h-[100px] text-sm"
                />
                <button type="submit" className="btn-primary text-xs py-2 px-4">Post Review</button>
              </form>
            )}

            <div className="space-y-4">
              {reviews.length > 0 ? (
                reviews.map((r) => {
                  const isAuthor = user && user.id === r.user_id;
                  const isEditing = editingReviewId === r.id;

                  return (
                    <div key={r.id} className="card p-5 space-y-3">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-3">
                          {r.user_avatar ? (
                            <img src={r.user_avatar} alt={r.username} className="w-9 h-9 rounded-full object-cover border border-[var(--color-border)]" />
                          ) : (
                            <div className="w-9 h-9 rounded-full bg-[var(--color-surface-2)] flex items-center justify-center font-bold text-sm text-[var(--color-text)] border border-[var(--color-border)]">
                              {(r.username || 'U').charAt(0).toUpperCase()}
                            </div>
                          )}
                          <div>
                            <div className="font-bold text-sm text-[var(--color-text)]">{r.username || 'CineMatch User'}</div>
                            <div className="text-[11px] text-[var(--color-text-dim)]">
                              {new Date(r.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                              {r.updated_at && <span className="ml-1 text-gray-500">(edited)</span>}
                            </div>
                          </div>
                        </div>

                        {isAuthor && (
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                setEditingReviewId(r.id);
                                setEditReviewContent(r.content);
                              }}
                              className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-primary-light)] font-semibold p-1"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteReview(r.id)}
                              className="text-xs text-rose-500 hover:text-rose-400 font-semibold p-1"
                            >
                              <TrashIcon className="w-4 h-4" />
                            </button>
                          </div>
                        )}
                      </div>

                      {isEditing ? (
                        <div className="space-y-3 pt-2">
                          <textarea
                            value={editReviewContent}
                            onChange={(e) => setEditReviewContent(e.target.value)}
                            className="input min-h-[80px] text-sm"
                          />
                          <div className="flex gap-2">
                            <button type="button" onClick={() => handleUpdateReview(r.id)} className="btn-primary text-xs py-1.5 px-3">
                              Save Changes
                            </button>
                            <button type="button" onClick={() => setEditingReviewId(null)} className="btn-ghost text-xs py-1.5 px-3">
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p className="text-sm text-[var(--color-text-muted)] leading-relaxed">{r.content}</p>
                      )}
                    </div>
                  );
                })
              ) : (
                <p className="text-sm text-[var(--color-text-dim)] py-4 italic">No reviews yet. Be the first to leave one!</p>
              )}
            </div>
          </section>
        </div>

        {/* Expanded Metadata Sidebar */}
        <div className="space-y-8">
          <div className="card p-6 space-y-4 border-[var(--color-primary)]/30">
            <h3 className="font-bold text-[var(--color-text)] text-lg font-['Outfit'] flex items-center gap-2">
              <PencilSquareIcon className="w-5 h-5 text-[var(--color-accent)]" /> Interactive Rating
            </h3>
            <RatingWidget initialRating={userRating} onRate={handleRate} disabled={!isAuthenticated} />

            <div className="pt-4 border-t border-[var(--color-border)] space-y-2">
              <label className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider block">Personal Notes</label>
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

          <div className="card p-6 space-y-3.5 text-xs">
            <h3 className="font-bold text-base text-[var(--color-text)] font-['Outfit'] mb-3 pb-2 border-b border-[var(--color-border)]">
              Complete Film Details
            </h3>

            <div className="flex justify-between py-1.5 border-b border-[var(--color-border)]">
              <span className="font-semibold text-[var(--color-text-dim)]">Director:</span>
              <span className="text-[var(--color-text)] font-bold text-right">{movie.director || 'N/A'}</span>
            </div>

            {movie.writers && movie.writers.length > 0 && (
              <div className="flex justify-between py-1.5 border-b border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Writers / Screenplay:</span>
                <span className="text-[var(--color-text)] font-medium text-right max-w-[60%]">{movie.writers.slice(0, 3).join(', ')}</span>
              </div>
            )}

            {movie.producers && movie.producers.length > 0 && (
              <div className="flex justify-between py-1.5 border-b border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Producers:</span>
                <span className="text-[var(--color-text)] font-medium text-right max-w-[60%]">{movie.producers.slice(0, 3).join(', ')}</span>
              </div>
            )}

            {movie.music_composers && movie.music_composers.length > 0 && (
              <div className="flex justify-between py-1.5 border-b border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Music Composer:</span>
                <span className="text-[var(--color-text)] font-medium text-right">{movie.music_composers.join(', ')}</span>
              </div>
            )}

            {movie.editors && movie.editors.length > 0 && (
              <div className="flex justify-between py-1.5 border-b border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Editor:</span>
                <span className="text-[var(--color-text)] font-medium text-right">{movie.editors.join(', ')}</span>
              </div>
            )}

            {movie.cinematographers && movie.cinematographers.length > 0 && (
              <div className="flex justify-between py-1.5 border-b border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Cinematography:</span>
                <span className="text-[var(--color-text)] font-medium text-right">{movie.cinematographers.join(', ')}</span>
              </div>
            )}

            <div className="flex justify-between py-1.5 border-b border-[var(--color-border)]">
              <span className="font-semibold text-[var(--color-text-dim)]">Production Companies:</span>
              <span className="text-[var(--color-text)] font-medium text-right max-w-[60%]">
                {movie.production_companies && movie.production_companies.length > 0 ? movie.production_companies.slice(0, 2).join(', ') : 'N/A'}
              </span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-[var(--color-border)]">
              <span className="font-semibold text-[var(--color-text-dim)]">Budget:</span>
              <span className="text-[var(--color-text)] font-semibold">{formatCurrency(movie.budget)}</span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-[var(--color-border)]">
              <span className="font-semibold text-[var(--color-text-dim)]">Box Office Revenue:</span>
              <span className="text-emerald-500 font-semibold">{formatCurrency(movie.revenue)}</span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-[var(--color-border)]">
              <span className="font-semibold text-[var(--color-text-dim)]">Spoken Languages:</span>
              <span className="text-[var(--color-text)] font-medium">{movie.spoken_languages?.join(', ') || 'English'}</span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-[var(--color-border)]">
              <span className="font-semibold text-[var(--color-text-dim)]">Streaming Providers:</span>
              <span className="text-[var(--color-accent)] font-semibold">Available to Stream</span>
            </div>
          </div>
        </div>
      </div>

      {recommendations.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6 pt-8 border-t border-[var(--color-border)]">
          <div className="flex items-center gap-3">
            <SparklesIcon className="w-6 h-6 text-[var(--color-accent)]" />
            <h2 className="section-title mb-0">More Movies You Might Enjoy</h2>
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

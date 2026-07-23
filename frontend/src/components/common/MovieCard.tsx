import React from 'react';
import { Link } from 'react-router-dom';
import { StarIcon, PlayIcon, HeartIcon, BookmarkIcon } from '@heroicons/react/24/solid';
import { HeartIcon as HeartOutline, BookmarkIcon as BookmarkOutline } from '@heroicons/react/24/outline';
import { Movie } from '../../types';
import { useMovieStore } from '../../store/movieStore';
import { useAuthStore } from '../../store/authStore';
import { userApi } from '../../api/client';
import toast from 'react-hot-toast';

interface MovieCardProps {
  movie: Movie;
}

export const MovieCard: React.FC<MovieCardProps> = ({ movie }) => {
  const { favoriteIds, watchlistIds, toggleFavoriteId, toggleWatchlistId, openTrailer } = useMovieStore();
  const { isAuthenticated } = useAuthStore();

  const isFav = favoriteIds.includes(movie.id);
  const isWatch = watchlistIds.includes(movie.id);

  const posterUrl = movie.poster_path
    ? (movie.poster_path.startsWith('http') ? movie.poster_path : `https://image.tmdb.org/t/p/w500${movie.poster_path}`)
    : 'https://via.placeholder.com/500x750?text=No+Poster';

  const handleFavorite = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      toast.error('Please sign in to save favorites');
      return;
    }
    toggleFavoriteId(movie.id);
    try {
      if (isFav) {
        await userApi.removeFavorite(movie.id);
        toast.success('Removed from favorites');
      } else {
        await userApi.addFavorite(movie.id);
        toast.success('Added to favorites');
      }
    } catch {
      toggleFavoriteId(movie.id); // rollback
    }
  };

  const handleWatchlist = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      toast.error('Please sign in to save watchlist');
      return;
    }
    toggleWatchlistId(movie.id);
    try {
      if (isWatch) {
        await userApi.removeWatchlist(movie.id);
        toast.success('Removed from watchlist');
      } else {
        await userApi.addWatchlist(movie.id);
        toast.success('Added to watchlist');
      }
    } catch {
      toggleWatchlistId(movie.id); // rollback
    }
  };

  const handlePlayTrailer = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (movie.trailer_key) {
      openTrailer(movie.trailer_key, movie.title);
    } else {
      toast.error('Trailer not available');
    }
  };

  return (
    <Link to={`/movies/${movie.id}`} className="movie-card group block">
      <div className="relative aspect-[2/3] rounded-xl overflow-hidden bg-[var(--color-surface-2)]">
        <img
          src={posterUrl}
          alt={movie.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
        />

        {/* Rating Pill */}
        <div className="absolute top-2 left-2 px-2 py-1 rounded-md bg-black/75 backdrop-blur-md flex items-center gap-1 text-xs font-bold text-[var(--color-accent)] border border-white/10">
          <StarIcon className="w-3.5 h-3.5" />
          {movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A'}
        </div>

        {/* Action Buttons */}
        <div className="absolute top-2 right-2 flex flex-col gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleFavorite}
            className={`p-2 rounded-full backdrop-blur-md transition-colors ${
              isFav ? 'bg-red-600 text-white' : 'bg-black/60 text-gray-300 hover:text-white'
            }`}
            title={isFav ? 'Remove Favorite' : 'Add Favorite'}
          >
            {isFav ? <HeartIcon className="w-4 h-4" /> : <HeartOutline className="w-4 h-4" />}
          </button>

          <button
            onClick={handleWatchlist}
            className={`p-2 rounded-full backdrop-blur-md transition-colors ${
              isWatch ? 'bg-[var(--color-accent)] text-black' : 'bg-black/60 text-gray-300 hover:text-white'
            }`}
            title={isWatch ? 'Remove Watchlist' : 'Add Watchlist'}
          >
            {isWatch ? <BookmarkIcon className="w-4 h-4" /> : <BookmarkOutline className="w-4 h-4" />}
          </button>
        </div>

        {/* Play Trailer Overlay */}
        {movie.trailer_key && (
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40">
            <button
              onClick={handlePlayTrailer}
              className="w-12 h-12 rounded-full bg-[var(--color-primary)] text-white flex items-center justify-center shadow-xl hover:scale-110 transition-transform"
              title="Play Trailer"
            >
              <PlayIcon className="w-6 h-6 ml-0.5" />
            </button>
          </div>
        )}

        {/* Overlay Info */}
        <div className="movie-card-overlay">
          <div className="text-xs font-medium text-gray-400 mb-1">
            {movie.release_year || 'Unknown Year'} {movie.runtime ? `• ${movie.runtime}m` : ''}
          </div>
          <h3 className="font-bold text-white text-sm line-clamp-1 group-hover:text-[var(--color-primary-light)] transition-colors">
            {movie.title}
          </h3>
          {movie.genres && movie.genres.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {movie.genres.slice(0, 2).map((g) => (
                <span key={g} className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-gray-300">
                  {g}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="mt-2">
        <h4 className="font-semibold text-white text-sm line-clamp-1 group-hover:text-[var(--color-primary-light)] transition-colors">
          {movie.title}
        </h4>
        <div className="flex justify-between items-center text-xs text-gray-400 mt-1">
          <span>{movie.release_year}</span>
          <span className="flex items-center gap-1 text-[var(--color-accent)] font-medium">
            <StarIcon className="w-3 h-3" />
            {movie.vote_average?.toFixed(1)}
          </span>
        </div>
      </div>
    </Link>
  );
};

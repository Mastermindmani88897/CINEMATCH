import React from 'react';
import { Link } from 'react-router-dom';
import { StarIcon, SparklesIcon, InformationCircleIcon } from '@heroicons/react/24/solid';
import type { RecommendationItem } from '../../types';

interface RecommendationCardProps {
  item: RecommendationItem;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({ item }) => {
  const posterUrl = item.poster_path
    ? (item.poster_path.startsWith('http') ? item.poster_path : `https://image.tmdb.org/t/p/w500${item.poster_path}`)
    : 'https://via.placeholder.com/500x750?text=No+Poster';

  const matchClass =
    item.match_percentage >= 80 ? 'high' : item.match_percentage >= 50 ? 'medium' : 'low';

  return (
    <div className="card p-4 flex flex-col sm:flex-row gap-4 hover:border-[var(--color-primary)]/50 transition-all">
      <Link to={`/movies/${item.movie_id}`} className="shrink-0">
        <img
          src={posterUrl}
          alt={item.title}
          className="w-24 sm:w-32 aspect-[2/3] object-cover rounded-lg shadow-md hover:scale-105 transition-transform"
        />
      </Link>

      <div className="flex-1 flex flex-col justify-between">
        <div>
          <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
            <span className={`match-badge ${matchClass}`}>
              <SparklesIcon className="w-3.5 h-3.5" />
              {item.match_percentage}% MATCH
            </span>
            <div className="flex items-center gap-1 text-xs text-[var(--color-accent)] font-bold">
              <StarIcon className="w-4 h-4" />
              {item.vote_average.toFixed(1)}
            </div>
          </div>

          <Link
            to={`/movies/${item.movie_id}`}
            className="font-bold text-lg text-white hover:text-[var(--color-primary-light)] transition-colors line-clamp-1 font-['Outfit']"
          >
            {item.title}
          </Link>

          <div className="text-xs text-gray-400 mt-0.5">
            {item.release_year} {item.genres && item.genres.length > 0 ? `• ${item.genres.slice(0, 3).join(', ')}` : ''}
          </div>

          {item.explanation && (
            <div className="mt-3 p-2.5 rounded-lg bg-[var(--color-surface-2)] border border-[var(--color-border)] text-xs text-gray-300 leading-relaxed flex items-start gap-2">
              <InformationCircleIcon className="w-4 h-4 text-[var(--color-accent)] shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-gray-200">Why recommended: </span>
                {item.explanation}
              </div>
            </div>
          )}
        </div>

        <div className="mt-4 flex items-center justify-between pt-2 border-t border-[var(--color-border)]">
          <span className="text-[11px] text-gray-400 font-mono">
            Cosine Similarity: {item.similarity_score.toFixed(4)}
          </span>
          <Link
            to={`/movies/${item.movie_id}`}
            className="text-xs font-semibold text-[var(--color-primary-light)] hover:underline flex items-center gap-1"
          >
            View Details &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
};

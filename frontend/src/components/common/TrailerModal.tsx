import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useMovieStore } from '../../store/movieStore';

export const TrailerModal: React.FC = () => {
  const { activeTrailerKey, activeTrailerTitle, closeTrailer } = useMovieStore();

  if (!activeTrailerKey) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-4xl bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[var(--color-border)] flex items-center justify-between">
          <h3 className="font-bold text-white text-lg font-['Outfit'] line-clamp-1">
            {activeTrailerTitle || 'Official Trailer'}
          </h3>
          <button
            onClick={closeTrailer}
            className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-[var(--color-surface-2)] transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Video Embed */}
        <div className="relative aspect-video w-full bg-black">
          <iframe
            src={`https://www.youtube.com/embed/${activeTrailerKey}?autoplay=1&rel=0`}
            title={activeTrailerTitle || 'Movie Trailer'}
            className="w-full h-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      </div>
    </div>
  );
};

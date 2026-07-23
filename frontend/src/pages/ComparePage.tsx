import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { movieApi, recApi } from '../api/client';
import type { Movie } from '../types';
import { AdjustmentsHorizontalIcon } from '@heroicons/react/24/solid';

export const ComparePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const m1Id = searchParams.get('m1');
  const m2Id = searchParams.get('m2');

  const [movie1, setMovie1] = useState<Movie | null>(null);
  const [movie2, setMovie2] = useState<Movie | null>(null);
  const [similarityScore, setSimilarityScore] = useState<number | null>(null);

  useEffect(() => {
    const fetchComparison = async () => {
      if (!m1Id) return;
      try {
        const m1 = await movieApi.getMovieById(parseInt(m1Id));
        setMovie1(m1);

        if (m2Id) {
          const m2 = await movieApi.getMovieById(parseInt(m2Id));
          setMovie2(m2);

          try {
            const exp = await recApi.getExplanation(m1.id, m2.id);
            setSimilarityScore(exp.similarity_score);
          } catch {}
        }
      } catch (err) {
        console.error('Failed comparison fetch', err);
      }
    };
    fetchComparison();
  }, [m1Id, m2Id]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white font-['Outfit'] flex items-center justify-center gap-2">
          <AdjustmentsHorizontalIcon className="w-8 h-8 text-[var(--color-primary-light)]" />
          Side-by-Side Movie Comparison
        </h1>
        <p className="text-gray-400 text-sm">Compare ratings, popularity, runtime, genres, and ML similarity</p>
      </div>

      {similarityScore !== null && (
        <div className="card p-4 text-center max-w-md mx-auto border-amber-500/30">
          <span className="text-xs font-bold text-amber-400 uppercase tracking-wider block">ML Content Similarity Score</span>
          <div className="text-3xl font-black text-white font-['Outfit'] mt-1">{(similarityScore * 100).toFixed(1)}% Match</div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {movie1 ? (
          <div className="card p-6 space-y-4">
            <img src={movie1.poster_path ? `https://image.tmdb.org/t/p/w500${movie1.poster_path}` : ''} alt={movie1.title} className="w-40 aspect-[2/3] object-cover rounded-xl mx-auto" />
            <h2 className="text-2xl font-bold text-white text-center font-['Outfit']">{movie1.title}</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-gray-400">Rating:</span>
                <span className="text-[var(--color-accent)] font-bold">{movie1.vote_average.toFixed(1)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-gray-400">Release Year:</span>
                <span className="text-white">{movie1.release_year}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-gray-400">Runtime:</span>
                <span className="text-white">{movie1.runtime}m</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-gray-400">Popularity:</span>
                <span className="text-white">{movie1.popularity.toFixed(1)}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="card p-12 text-center text-gray-500">Select first movie to compare</div>
        )}

        {movie2 ? (
          <div className="card p-6 space-y-4">
            <img src={movie2.poster_path ? `https://image.tmdb.org/t/p/w500${movie2.poster_path}` : ''} alt={movie2.title} className="w-40 aspect-[2/3] object-cover rounded-xl mx-auto" />
            <h2 className="text-2xl font-bold text-white text-center font-['Outfit']">{movie2.title}</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-gray-400">Rating:</span>
                <span className="text-[var(--color-accent)] font-bold">{movie2.vote_average.toFixed(1)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-gray-400">Release Year:</span>
                <span className="text-white">{movie2.release_year}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-gray-400">Runtime:</span>
                <span className="text-white">{movie2.runtime}m</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-gray-400">Popularity:</span>
                <span className="text-white">{movie2.popularity.toFixed(1)}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="card p-12 text-center text-gray-500">Pass m2=movie_id in URL to compare a second movie</div>
        )}
      </div>
    </div>
  );
};

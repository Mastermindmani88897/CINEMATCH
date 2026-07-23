import React from 'react';

export const MovieCardSkeleton: React.FC = () => {
  return (
    <div className="space-y-2">
      <div className="skeleton aspect-[2/3] w-full rounded-xl" />
      <div className="skeleton h-4 w-3/4 rounded" />
      <div className="skeleton h-3 w-1/2 rounded" />
    </div>
  );
};

export const MovieGridSkeleton: React.FC<{ count?: number }> = ({ count = 10 }) => {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <MovieCardSkeleton key={i} />
      ))}
    </div>
  );
};

export const RecommendationCardSkeleton: React.FC = () => {
  return (
    <div className="card p-4 flex gap-4">
      <div className="skeleton w-24 sm:w-32 aspect-[2/3] rounded-lg shrink-0" />
      <div className="flex-1 space-y-3">
        <div className="skeleton h-5 w-1/4 rounded" />
        <div className="skeleton h-6 w-3/4 rounded" />
        <div className="skeleton h-4 w-1/3 rounded" />
        <div className="skeleton h-16 w-full rounded-lg" />
      </div>
    </div>
  );
};

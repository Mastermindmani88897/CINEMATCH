import React from 'react';
import { Link } from 'react-router-dom';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4 space-y-6">
      <div className="text-8xl font-black text-[var(--color-primary-light)] font-['Outfit'] animate-pulse">404</div>
      <h1 className="text-3xl font-extrabold text-white font-['Outfit']">Scene Not Found</h1>
      <p className="text-gray-400 max-w-md text-sm">
        The page or movie reel you are looking for has been lost in the cutting room floor.
      </p>
      <Link to="/" className="btn-primary">
        Back to Home Reel
      </Link>
    </div>
  );
};

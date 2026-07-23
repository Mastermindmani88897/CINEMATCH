import React from 'react';
import { Link } from 'react-router-dom';
import { FilmIcon } from '@heroicons/react/24/outline';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[var(--color-surface)] border-t border-[var(--color-border)] mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="space-y-4 md:col-span-1">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center">
                <FilmIcon className="w-5 h-5 text-white" />
              </div>
              <span className="font-extrabold text-lg tracking-tight text-white font-['Outfit']">
                Cine<span className="gradient-text">Match</span> AI
              </span>
            </Link>
            <p className="text-sm text-gray-400 leading-relaxed">
              Intelligent Hybrid Movie Recommendation Platform powered by Machine Learning, NLP & Sentence Transformers.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="font-semibold text-white mb-4 text-sm font-['Outfit'] uppercase tracking-wider">Navigation</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><Link to="/" className="hover:text-white transition-colors">Home</Link></li>
              <li><Link to="/recommendations" className="hover:text-white transition-colors">AI Recommender</Link></li>
              <li><Link to="/search" className="hover:text-white transition-colors">Semantic Search</Link></li>
              <li><Link to="/compare" className="hover:text-white transition-colors">Movie Comparison</Link></li>
            </ul>
          </div>

          {/* Machine Learning Features */}
          <div>
            <h4 className="font-semibold text-white mb-4 text-sm font-['Outfit'] uppercase tracking-wider">ML Architecture</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>Content-Based (TF-IDF)</li>
              <li>Semantic (MiniLM-L6)</li>
              <li>Popularity & Bayesian Rating</li>
              <li>Mood & Genre Filtering</li>
              <li>Personalized Taste Analysis</li>
            </ul>
          </div>

          {/* Stack */}
          <div>
            <h4 className="font-semibold text-white mb-4 text-sm font-['Outfit'] uppercase tracking-wider">Tech Stack</h4>
            <div className="flex flex-wrap gap-2">
              {['FastAPI', 'React', 'TypeScript', 'Tailwind', 'scikit-learn', 'PyTorch', 'PostgreSQL', 'Zustand'].map((tech) => (
                <span key={tech} className="text-xs px-2.5 py-1 rounded-md bg-[var(--color-surface-2)] text-gray-300 border border-[var(--color-border)]">
                  {tech}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="border-t border-[var(--color-border)] mt-8 pt-8 flex flex-col sm:flex-row justify-between items-center text-xs text-gray-500 gap-4">
          <p>© {new Date().getFullYear()} CineMatch AI. Built for portfolio & production deployment.</p>
          <div className="flex gap-6">
            <a href="https://developer.themoviedb.org/docs" target="_blank" rel="noreferrer" className="hover:text-gray-400">Powered by TMDB API</a>
            <a href="/api/docs" target="_blank" rel="noreferrer" className="hover:text-gray-400">FastAPI Swagger Docs</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

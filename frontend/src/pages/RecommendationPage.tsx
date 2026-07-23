import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SparklesIcon, FireIcon, HeartIcon, FilmIcon, UserIcon } from '@heroicons/react/24/outline';
import { recApi, movieApi } from '../api/client';
import type { RecommendationItem } from '../types';
import { RecommendationCard } from '../components/common/RecommendationCard';
import { RecommendationCardSkeleton } from '../components/common/Skeleton';
import { useAuthStore } from '../store/authStore';

type AlgoType = 'mood' | 'genre' | 'popularity' | 'semantic' | 'personalized' | 'content';

export const RecommendationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialMood = searchParams.get('mood') || 'happy';

  const [activeTab, setActiveTab] = useState<AlgoType>(initialMood ? 'mood' : 'popularity');
  const [selectedMood, setSelectedMood] = useState(initialMood);
  const [selectedGenres, setSelectedGenres] = useState<string[]>(['Action']);
  const [semanticQuery, setSemanticQuery] = useState('emotional sci-fi space movies');
  const seedMovieId = 1;
  const [results, setResults] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [allGenres, setAllGenres] = useState<string[]>([]);
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    movieApi.getGenres().then(setAllGenres).catch(console.error);
  }, []);

  useEffect(() => {
    fetchRecommendations();
  }, [activeTab, selectedMood, selectedGenres, seedMovieId]);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      let res;
      if (activeTab === 'mood') {
        res = await recApi.getMoodRecs(selectedMood);
      } else if (activeTab === 'genre') {
        res = await recApi.getGenreRecs(selectedGenres.join(','));
      } else if (activeTab === 'popularity') {
        res = await recApi.getPopularRecs('weighted');
      } else if (activeTab === 'personalized' && isAuthenticated) {
        res = await recApi.getPersonalizedRecs();
      } else if (activeTab === 'content') {
        res = await recApi.getContentRecs(seedMovieId);
      } else if (activeTab === 'semantic' && semanticQuery) {
        res = await recApi.postSemanticSearch(semanticQuery);
      }
      if (res) setResults(res.recommendations);
    } catch (err) {
      console.error('Failed to load recommendations', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSemanticSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchRecommendations();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--color-primary)]/10 text-[var(--color-primary-light)] text-xs font-bold uppercase tracking-wider">
          <SparklesIcon className="w-4 h-4" /> Hybrid ML Recommender Engine
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-white font-['Outfit']">
          AI Recommendation Center
        </h1>
        <p className="text-gray-400 text-sm sm:text-base">
          Choose from 6 specialized recommendation algorithms powered by TF-IDF, Cosine Similarity, and Sentence Transformers.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-2 border-b border-[var(--color-border)] pb-4">
        {[
          { id: 'mood', label: 'Mood Based', icon: HeartIcon },
          { id: 'genre', label: 'Genre Based', icon: FilmIcon },
          { id: 'popularity', label: 'Popularity & Rating', icon: FireIcon },
          { id: 'semantic', label: 'Semantic AI Search', icon: SparklesIcon },
          { id: 'personalized', label: 'Personalized Taste', icon: UserIcon },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as AlgoType)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all ${
                activeTab === tab.id
                  ? 'bg-[var(--color-primary)] text-white shadow-lg shadow-[var(--color-primary)]/30'
                  : 'bg-[var(--color-surface-2)] text-gray-400 hover:text-white hover:bg-[var(--color-surface-3)]'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="card p-6 max-w-4xl mx-auto">
        {activeTab === 'mood' && (
          <div className="space-y-4">
            <h3 className="font-bold text-white text-sm">Select Mood:</h3>
            <div className="flex flex-wrap gap-3">
              {['happy', 'sad', 'romantic', 'action', 'family', 'adventure', 'crime', 'horror', 'scifi'].map((m) => (
                <button
                  key={m}
                  onClick={() => setSelectedMood(m)}
                  className={`genre-pill text-xs capitalize ${selectedMood === m ? 'active' : ''}`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'genre' && (
          <div className="space-y-4">
            <h3 className="font-bold text-white text-sm">Select Genres:</h3>
            <div className="flex flex-wrap gap-2">
              {allGenres.map((g) => (
                <button
                  key={g}
                  onClick={() =>
                    setSelectedGenres(
                      selectedGenres.includes(g)
                        ? selectedGenres.filter((x) => x !== g)
                        : [...selectedGenres, g]
                    )
                  }
                  className={`genre-pill text-xs ${selectedGenres.includes(g) ? 'active' : ''}`}
                >
                  {g}
                </button>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'semantic' && (
          <form onSubmit={handleSemanticSubmit} className="flex gap-3">
            <input
              type="text"
              value={semanticQuery}
              onChange={(e) => setSemanticQuery(e.target.value)}
              placeholder="e.g., 'funny detective movies with high stakes'..."
              className="input flex-1"
            />
            <button type="submit" className="btn-primary shrink-0">
              <SparklesIcon className="w-4 h-4" /> AI Search
            </button>
          </form>
        )}

        {activeTab === 'personalized' && !isAuthenticated && (
          <div className="text-center py-4 text-gray-400 text-sm">
            Please sign in to view your personalized recommendations based on watch history & favorites.
          </div>
        )}
      </div>

      <div className="max-w-4xl mx-auto space-y-4">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => <RecommendationCardSkeleton key={i} />)
        ) : results.length > 0 ? (
          results.map((item) => <RecommendationCard key={item.movie_id} item={item} />)
        ) : (
          <div className="text-center py-12 text-gray-400">No recommendations found for this criteria.</div>
        )}
      </div>
    </div>
  );
};

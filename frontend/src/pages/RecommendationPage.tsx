import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SparklesIcon, FireIcon, HeartIcon, FilmIcon, GlobeAsiaAustraliaIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { recApi, movieApi } from '../api/client';
import type { RecommendationItem } from '../types';
import { RecommendationCard } from '../components/common/RecommendationCard';
import { RecommendationCardSkeleton } from '../components/common/Skeleton';

type AlgoType = 'industry' | 'mood' | 'genre' | 'popularity' | 'semantic';

const INDUSTRIES = [
  { id: 'tollywood', name: 'Tollywood (Telugu)' },
  { id: 'bollywood', name: 'Bollywood (Hindi)' },
  { id: 'kollywood', name: 'Kollywood (Tamil)' },
  { id: 'mollywood', name: 'Mollywood (Malayalam)' },
  { id: 'sandalwood', name: 'Sandalwood (Kannada)' },
  { id: 'hollywood', name: 'Hollywood (English)' },
  { id: 'korean', name: 'Korean Cinema' },
  { id: 'anime', name: 'Anime' },
  { id: 'japanese', name: 'Japanese' },
  { id: 'chinese', name: 'Chinese' },
  { id: 'international', name: 'International Cinema' },
];

const MOODS = [
  'happy', 'sad', 'romantic', 'action', 'motivational',
  'thriller', 'dark', 'comedy', 'family', 'adventure',
  'crime', 'horror', 'scifi'
];

export const RecommendationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialMood = searchParams.get('mood') || 'happy';

  const [activeTab, setActiveTab] = useState<AlgoType>(initialMood && MOODS.includes(initialMood.toLowerCase()) ? 'mood' : 'industry');
  
  // Isolated per-tab states
  const [selectedIndustry, setSelectedIndustry] = useState('tollywood');
  const [selectedMood, setSelectedMood] = useState(initialMood.toLowerCase());
  const [selectedGenres, setSelectedGenres] = useState<string[]>(['Action']);
  const [popularityMode, setPopularityMode] = useState<'weighted' | 'trending' | 'popular' | 'top_rated'>('weighted');
  const [semanticQuery, setSemanticQuery] = useState('emotional sci-fi space adventure');

  const [results, setResults] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [allGenres, setAllGenres] = useState<string[]>([]);

  useEffect(() => {
    movieApi.getGenres().then(setAllGenres).catch(console.error);
  }, []);

  // Handle Tab Switching: Automatically reset states to ensure zero filter leakage
  const handleTabChange = (newTab: AlgoType) => {
    setActiveTab(newTab);
    setResults([]);
    // Reset defaults to guarantee clean state
    if (newTab === 'industry') setSelectedIndustry('tollywood');
    if (newTab === 'mood') setSelectedMood('happy');
    if (newTab === 'genre') setSelectedGenres(['Action']);
    if (newTab === 'popularity') setPopularityMode('weighted');
    if (newTab === 'semantic') setSemanticQuery('');
  };

  const handleResetFilters = () => {
    setResults([]);
    if (activeTab === 'industry') setSelectedIndustry('tollywood');
    if (activeTab === 'mood') setSelectedMood('happy');
    if (activeTab === 'genre') setSelectedGenres([]);
    if (activeTab === 'popularity') setPopularityMode('weighted');
    if (activeTab === 'semantic') setSemanticQuery('');
  };

  useEffect(() => {
    fetchRecommendations();
  }, [activeTab, selectedIndustry, selectedMood, selectedGenres, popularityMode]);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      let res;
      if (activeTab === 'industry') {
        res = await recApi.getIndustryRecs(selectedIndustry);
      } else if (activeTab === 'mood') {
        res = await recApi.getMoodRecs(selectedMood);
      } else if (activeTab === 'genre') {
        if (selectedGenres.length === 0) {
          setResults([]);
          setLoading(false);
          return;
        }
        res = await recApi.getGenreRecs(selectedGenres.join(','));
      } else if (activeTab === 'popularity') {
        res = await recApi.getPopularRecs(popularityMode);
      } else if (activeTab === 'semantic' && semanticQuery.trim()) {
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
    if (semanticQuery.trim()) {
      fetchRecommendations();
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--color-primary)]/10 text-[var(--color-primary-light)] text-xs font-bold uppercase tracking-wider border border-[var(--color-primary)]/30">
          <SparklesIcon className="w-4 h-4 text-[var(--color-accent)]" /> CineMatch AI Hybrid Engine
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-white font-['Outfit']">
          Movie Recommendation Hub
        </h1>
        <p className="text-gray-400 text-sm sm:text-base">
          Explore movies tailored by industry, emotional mood, specific genres, global popularity, or natural language AI search.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap items-center justify-center gap-2 border-b border-[var(--color-border)] pb-4">
        {[
          { id: 'industry', label: 'By Industry / Region', icon: GlobeAsiaAustraliaIcon },
          { id: 'mood', label: 'Mood Based', icon: HeartIcon },
          { id: 'genre', label: 'Genre Based', icon: FilmIcon },
          { id: 'popularity', label: 'Popularity & Rating', icon: FireIcon },
          { id: 'semantic', label: 'Semantic AI Search', icon: SparklesIcon },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id as AlgoType)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all ${
                isActive
                  ? 'bg-[var(--color-primary)] text-white shadow-lg shadow-[var(--color-primary)]/30'
                  : 'bg-[var(--color-surface-2)] text-gray-400 hover:text-white hover:bg-[var(--color-surface-3)] border border-[var(--color-border)]'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Filter Controls */}
      <div className="card p-6 max-w-4xl mx-auto space-y-6">
        <div className="flex justify-between items-center pb-3 border-b border-[var(--color-border)]">
          <span className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
            Active Mode: <strong className="text-[var(--color-accent)] capitalize">{activeTab} Filter</strong>
          </span>
          <button
            onClick={handleResetFilters}
            className="flex items-center gap-1 text-xs font-semibold text-gray-400 hover:text-white transition-colors"
          >
            <ArrowPathIcon className="w-3.5 h-3.5" /> Reset Filters
          </button>
        </div>

        {activeTab === 'industry' && (
          <div className="space-y-4">
            <h3 className="font-bold text-[var(--color-text)] text-sm">Select Industry / Regional Cinema:</h3>
            <div className="flex flex-wrap gap-2.5">
              {INDUSTRIES.map((ind) => (
                <button
                  key={ind.id}
                  onClick={() => setSelectedIndustry(ind.id)}
                  className={`genre-pill text-xs capitalize ${selectedIndustry === ind.id ? 'active' : ''}`}
                >
                  {ind.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'mood' && (
          <div className="space-y-4">
            <h3 className="font-bold text-[var(--color-text)] text-sm">Select Mood:</h3>
            <div className="flex flex-wrap gap-2.5">
              {MOODS.map((m) => (
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
            <div className="flex justify-between items-center">
              <h3 className="font-bold text-[var(--color-text)] text-sm">Select Genres (Multi-Select Supported):</h3>
              {selectedGenres.length > 0 && (
                <span className="text-xs text-[var(--color-primary-light)] font-bold">
                  {selectedGenres.length} Selected ({selectedGenres.join(' + ')})
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {allGenres.map((g) => (
                <button
                  key={g}
                  onClick={() =>
                    setSelectedGenres((prev) =>
                      prev.includes(g) ? prev.filter((x) => x !== g) : [...prev, g]
                    )
                  }
                  className={`genre-pill text-xs ${selectedGenres.includes(g) ? 'active shadow-sm' : ''}`}
                >
                  {selectedGenres.includes(g) ? `✓ ${g}` : g}
                </button>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'popularity' && (
          <div className="space-y-4">
            <h3 className="font-bold text-white text-sm">Select Ranking Metric:</h3>
            <div className="flex flex-wrap gap-3">
              {[
                { id: 'weighted', name: 'Weighted Rating' },
                { id: 'trending', name: 'Trending Right Now' },
                { id: 'popular', name: 'Most Popular' },
                { id: 'top_rated', name: 'Top Rated Classics' },
              ].map((pm) => (
                <button
                  key={pm.id}
                  onClick={() => setPopularityMode(pm.id as any)}
                  className={`genre-pill text-xs ${popularityMode === pm.id ? 'active' : ''}`}
                >
                  {pm.name}
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
              placeholder="Describe what movie you want to watch (e.g. 'mind-bending sci-fi thriller in space')..."
              className="input flex-1 text-sm"
            />
            <button type="submit" className="btn-primary shrink-0 text-xs py-2.5 px-5">
              <SparklesIcon className="w-4 h-4" /> AI Search
            </button>
          </form>
        )}
      </div>

      {/* Results */}
      <div className="max-w-4xl mx-auto space-y-4">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => <RecommendationCardSkeleton key={i} />)
        ) : results.length > 0 ? (
          results.map((item) => <RecommendationCard key={item.movie_id} item={item} />)
        ) : (
          <div className="text-center py-12 text-gray-400 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] p-8">
            <div className="text-4xl mb-2">🎬</div>
            <h3 className="text-lg font-bold text-white font-['Outfit']">No Recommendations Found</h3>
            <p className="text-xs text-gray-400 mt-1">Try selecting a different filter or reset your choices.</p>
            <button onClick={handleResetFilters} className="btn-ghost text-xs mt-4">Reset Filters</button>
          </div>
        )}
      </div>
    </div>
  );
};

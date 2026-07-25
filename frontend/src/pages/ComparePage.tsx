import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { movieApi, searchApi } from '../api/client';
import type { Movie } from '../types';
import { AdjustmentsHorizontalIcon, ArrowsRightLeftIcon, XMarkIcon, MagnifyingGlassIcon, SparklesIcon } from '@heroicons/react/24/solid';

export const ComparePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const m1Id = searchParams.get('m1');
  const m2Id = searchParams.get('m2');

  const [movie1, setMovie1] = useState<Movie | null>(null);
  const [movie2, setMovie2] = useState<Movie | null>(null);
  const [similarityScore, setSimilarityScore] = useState<number | null>(null);

  // Search states for Dual Autocomplete
  const [q1, setQ1] = useState('');
  const [q2, setQ2] = useState('');
  const [sug1, setSug1] = useState<Movie[]>([]);
  const [sug2, setSug2] = useState<Movie[]>([]);
  const [openSug1, setOpenSug1] = useState(false);
  const [openSug2, setOpenSug2] = useState(false);

  // Recently compared movies in local storage
  const [recentCompares, setRecentCompares] = useState<{ id1: number; title1: string; id2: number; title2: string }[]>([]);

  const sugRef1 = useRef<HTMLDivElement>(null);
  const sugRef2 = useRef<HTMLDivElement>(null);

  // Load recently compared from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem('cinematch_recent_compares');
      if (saved) setRecentCompares(JSON.parse(saved));
    } catch {}
  }, []);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (sugRef1.current && !sugRef1.current.contains(e.target as Node)) setOpenSug1(false);
      if (sugRef2.current && !sugRef2.current.contains(e.target as Node)) setOpenSug2(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch Movie A & Movie B when URL search params change
  useEffect(() => {
    const fetchComparison = async () => {
      if (!m1Id) {
        setMovie1(null);
        setSimilarityScore(null);
        return;
      }
      try {
        const m1 = await movieApi.getMovieById(parseInt(m1Id));
        setMovie1(m1);

        if (m2Id) {
          const m2 = await movieApi.getMovieById(parseInt(m2Id));
          setMovie2(m2);

          const genreOverlap = (m1.genres || []).filter((g: string) => (m2.genres || []).includes(g)).length;
          const totalGenres = new Set([...(m1.genres || []), ...(m2.genres || [])]).size || 1;
          const ratingDiff = Math.abs((m1.vote_average || 0) - (m2.vote_average || 0));
          const score = Math.max(0.1, (genreOverlap / totalGenres) * 0.7 + Math.max(0, 1 - ratingDiff / 5) * 0.3);
          setSimilarityScore(score);

          // Save to recent compares
          const newEntry = { id1: m1.id, title1: m1.title, id2: m2.id, title2: m2.title };
          setRecentCompares((prev) => {
            const filtered = prev.filter((p) => !(p.id1 === m1.id && p.id2 === m2.id));
            const updated = [newEntry, ...filtered].slice(0, 5);
            localStorage.setItem('cinematch_recent_compares', JSON.stringify(updated));
            return updated;
          });
        } else {
          setMovie2(null);
          setSimilarityScore(null);
        }
      } catch (err) {
        console.error('Failed comparison fetch', err);
      }
    };
    fetchComparison();
  }, [m1Id, m2Id]);

  // Autocomplete search for Movie A
  useEffect(() => {
    if (!q1.trim() || q1.length < 2) {
      setSug1([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await searchApi.search(q1, { per_page: 6 });
        setSug1(res.items);
        setOpenSug1(true);
      } catch {}
    }, 250);
    return () => clearTimeout(timer);
  }, [q1]);

  // Autocomplete search for Movie B
  useEffect(() => {
    if (!q2.trim() || q2.length < 2) {
      setSug2([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await searchApi.search(q2, { per_page: 6 });
        setSug2(res.items);
        setOpenSug2(true);
      } catch {}
    }, 250);
    return () => clearTimeout(timer);
  }, [q2]);

  const selectMovieA = (m: Movie) => {
    setMovie1(m);
    setQ1('');
    setOpenSug1(false);
    if (movie2) {
      setSearchParams({ m1: m.id.toString(), m2: movie2.id.toString() });
    } else {
      setSearchParams({ m1: m.id.toString() });
    }
  };

  const selectMovieB = (m: Movie) => {
    setMovie2(m);
    setQ2('');
    setOpenSug2(false);
    if (movie1) {
      setSearchParams({ m1: movie1.id.toString(), m2: m.id.toString() });
    }
  };

  const handleSwap = () => {
    if (!movie1 && !movie2) return;
    const temp1 = movie1;
    const temp2 = movie2;
    setMovie1(temp2);
    setMovie2(temp1);
    if (temp2 && temp1) {
      setSearchParams({ m1: temp2.id.toString(), m2: temp1.id.toString() });
    } else if (temp2) {
      setSearchParams({ m1: temp2.id.toString() });
    }
  };

  const clearMovieA = () => {
    setMovie1(null);
    setSimilarityScore(null);
    if (movie2) {
      setSearchParams({ m1: movie2.id.toString() });
    } else {
      setSearchParams({});
    }
  };

  const clearMovieB = () => {
    setMovie2(null);
    setSimilarityScore(null);
    if (movie1) {
      setSearchParams({ m1: movie1.id.toString() });
    }
  };

  const POSTER_FALLBACK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='500' height='750' viewBox='0 0 500 750'%3E%3Crect width='500' height='750' fill='%231a1a26'/%3E%3Ctext x='250' y='375' font-family='Inter,sans-serif' font-size='24' fill='%235a5a72' text-anchor='middle' dominant-baseline='middle'%3E🎬%3C/text%3E%3C/svg%3E";

  const getPoster = (m: Movie | null) => {
    if (!m || !m.poster_path) return POSTER_FALLBACK;
    return m.poster_path.startsWith('http') ? m.poster_path : `https://image.tmdb.org/t/p/w500${m.poster_path}`;
  };

  const formatCurrency = (val?: number) => {
    if (!val || val === 0) return 'N/A';
    return `$${(val / 1000000).toFixed(1)}M`;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="text-center space-y-2 max-w-3xl mx-auto">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-[var(--color-text)] font-['Outfit'] flex items-center justify-center gap-2">
          <AdjustmentsHorizontalIcon className="w-8 h-8 text-[var(--color-primary-light)]" />
          Side-by-Side Movie Comparison
        </h1>
        <p className="text-[var(--color-text-muted)] text-sm sm:text-base">
          Search and pick any two movies from 15,000+ films to compare ratings, box office, cast, crew, and compatibility.
        </p>
      </div>

      {/* Dual Movie Search Inputs & Swap Controls */}
      <div className="card p-6 grid grid-cols-1 md:grid-cols-12 gap-4 items-center relative">
        {/* Movie A Search */}
        <div className="md:col-span-5 relative" ref={sugRef1}>
          <label className="text-xs font-bold uppercase tracking-wider text-[var(--color-primary-light)] block mb-1.5">
            Movie A (First Selection):
          </label>
          {movie1 ? (
            <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-primary)]/40">
              <div className="flex items-center gap-3">
                <img src={getPoster(movie1)} alt={movie1.title} className="w-10 h-14 object-cover rounded-md" />
                <div>
                  <div className="font-bold text-sm text-[var(--color-text)] line-clamp-1">{movie1.title}</div>
                  <div className="text-xs text-[var(--color-accent)] font-semibold">{movie1.release_year} • ⭐ {movie1.vote_average.toFixed(1)}</div>
                </div>
              </div>
              <button type="button" onClick={clearMovieA} className="p-1 text-gray-400 hover:text-rose-500">
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
          ) : (
            <div className="relative">
              <input
                type="text"
                value={q1}
                onChange={(e) => setQ1(e.target.value)}
                placeholder="Search Movie A (e.g. Inception, Baahubali)..."
                className="input text-sm pl-10"
              />
              <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute left-3 top-3" />
            </div>
          )}

          {/* Autocomplete Dropdown A */}
          {openSug1 && sug1.length > 0 && !movie1 && (
            <div className="absolute z-30 left-0 right-0 mt-1 card shadow-2xl bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden divide-y divide-[var(--color-border)]">
              {sug1.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => selectMovieA(m)}
                  className="w-full p-2.5 flex items-center gap-3 text-left hover:bg-[var(--color-surface-2)] transition-colors"
                >
                  <img src={getPoster(m)} alt={m.title} className="w-8 h-12 object-cover rounded" />
                  <div>
                    <div className="font-bold text-xs text-[var(--color-text)]">{m.title}</div>
                    <div className="text-[11px] text-[var(--color-text-dim)]">{m.release_year} • ⭐ {m.vote_average.toFixed(1)}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Swap Control Button */}
        <div className="md:col-span-2 flex justify-center py-2">
          <button
            type="button"
            onClick={handleSwap}
            disabled={!movie1 && !movie2}
            className="p-3 rounded-full bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[var(--color-primary-light)] hover:scale-110 hover:border-[var(--color-primary)] transition-all shadow-md"
            title="Swap Movie A and Movie B"
          >
            <ArrowsRightLeftIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Movie B Search */}
        <div className="md:col-span-5 relative" ref={sugRef2}>
          <label className="text-xs font-bold uppercase tracking-wider text-[var(--color-accent)] block mb-1.5">
            Movie B (Second Selection):
          </label>
          {movie2 ? (
            <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--color-surface-2)] border border-amber-500/40">
              <div className="flex items-center gap-3">
                <img src={getPoster(movie2)} alt={movie2.title} className="w-10 h-14 object-cover rounded-md" />
                <div>
                  <div className="font-bold text-sm text-[var(--color-text)] line-clamp-1">{movie2.title}</div>
                  <div className="text-xs text-[var(--color-accent)] font-semibold">{movie2.release_year} • ⭐ {movie2.vote_average.toFixed(1)}</div>
                </div>
              </div>
              <button type="button" onClick={clearMovieB} className="p-1 text-gray-400 hover:text-rose-500">
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
          ) : (
            <div className="relative">
              <input
                type="text"
                value={q2}
                onChange={(e) => setQ2(e.target.value)}
                placeholder="Search Movie B (e.g. Interstellar, RRR)..."
                className="input text-sm pl-10"
              />
              <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute left-3 top-3" />
            </div>
          )}

          {/* Autocomplete Dropdown B */}
          {openSug2 && sug2.length > 0 && !movie2 && (
            <div className="absolute z-30 left-0 right-0 mt-1 card shadow-2xl bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden divide-y divide-[var(--color-border)]">
              {sug2.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => selectMovieB(m)}
                  className="w-full p-2.5 flex items-center gap-3 text-left hover:bg-[var(--color-surface-2)] transition-colors"
                >
                  <img src={getPoster(m)} alt={m.title} className="w-8 h-12 object-cover rounded" />
                  <div>
                    <div className="font-bold text-xs text-[var(--color-text)]">{m.title}</div>
                    <div className="text-[11px] text-[var(--color-text-dim)]">{m.release_year} • ⭐ {m.vote_average.toFixed(1)}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recently Compared Chips */}
      {recentCompares.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 px-1 text-xs">
          <span className="font-bold text-[var(--color-text-dim)]">Recently Compared:</span>
          {recentCompares.map((rc, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setSearchParams({ m1: rc.id1.toString(), m2: rc.id2.toString() })}
              className="px-3 py-1 rounded-full bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-primary)] transition-all font-medium"
            >
              {rc.title1} <span className="text-[var(--color-primary-light)] font-bold">vs</span> {rc.title2}
            </button>
          ))}
        </div>
      )}

      {/* Overall Compatibility Banner */}
      {movie1 && movie2 && similarityScore !== null && (
        <div className="card p-6 text-center max-w-xl mx-auto border-amber-500/40 bg-gradient-to-r from-amber-500/10 via-[var(--color-surface-2)] to-amber-500/10">
          <div className="flex justify-center items-center gap-2 text-xs font-bold text-amber-500 dark:text-amber-400 uppercase tracking-wider mb-1">
            <SparklesIcon className="w-4 h-4" /> Feature & Genre Compatibility Score
          </div>
          <div className="text-4xl font-black text-[var(--color-text)] font-['Outfit'] mt-1">
            {(similarityScore * 100).toFixed(1)}% Match
          </div>
          <p className="text-xs text-[var(--color-text-muted)] mt-2">
            Calculated from shared genres, rating alignment, release era, and storytelling themes.
          </p>
        </div>
      )}

      {/* Side-by-Side Comparison Matrix */}
      {movie1 && movie2 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Movie A Card */}
          <div className="card p-6 space-y-6 border-[var(--color-primary)]/40 shadow-xl">
            <img src={getPoster(movie1)} alt={movie1.title} className="w-48 aspect-[2/3] object-cover rounded-xl mx-auto shadow-2xl border border-white/10" />
            <div className="text-center space-y-1">
              <h2 className="text-2xl font-bold text-[var(--color-text)] font-['Outfit']">{movie1.title}</h2>
              {movie1.tagline && <p className="italic text-xs text-[var(--color-text-muted)]">"{movie1.tagline}"</p>}
            </div>

            <div className="space-y-3 text-xs">
              <div className={`flex justify-between p-2.5 rounded-lg border ${movie1.vote_average >= movie2.vote_average ? 'bg-emerald-500/10 border-emerald-500/40' : 'border-[var(--color-border)]'}`}>
                <span className="font-semibold text-[var(--color-text-dim)]">IMDb/TMDB Rating:</span>
                <span className="font-bold text-[var(--color-accent)]">{movie1.vote_average.toFixed(1)} ⭐ {movie1.vote_average >= movie2.vote_average && '🏆'}</span>
              </div>

              <div className={`flex justify-between p-2.5 rounded-lg border ${movie1.popularity >= movie2.popularity ? 'bg-emerald-500/10 border-emerald-500/40' : 'border-[var(--color-border)]'}`}>
                <span className="font-semibold text-[var(--color-text-dim)]">Popularity Index:</span>
                <span className="font-semibold text-[var(--color-text)]">{movie1.popularity.toFixed(1)} {movie1.popularity >= movie2.popularity && '🔥'}</span>
              </div>

              <div className="flex justify-between p-2.5 rounded-lg border border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Release Year:</span>
                <span className="font-semibold text-[var(--color-text)]">{movie1.release_year}</span>
              </div>

              <div className={`flex justify-between p-2.5 rounded-lg border ${(movie1.runtime || 0) >= (movie2.runtime || 0) ? 'bg-amber-500/10 border-amber-500/40' : 'border-[var(--color-border)]'}`}>
                <span className="font-semibold text-[var(--color-text-dim)]">Runtime:</span>
                <span className="font-semibold text-[var(--color-text)]">{movie1.runtime} min</span>
              </div>

              <div className="flex justify-between p-2.5 rounded-lg border border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Genres:</span>
                <span className="font-semibold text-[var(--color-primary-light)] text-right max-w-[60%]">{movie1.genres?.join(', ')}</span>
              </div>

              <div className="flex justify-between p-2.5 rounded-lg border border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Director:</span>
                <span className="font-bold text-[var(--color-text)] text-right max-w-[60%]">{movie1.director || 'N/A'}</span>
              </div>

              <div className="flex justify-between p-2.5 rounded-lg border border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Writers:</span>
                <span className="font-medium text-[var(--color-text)] text-right max-w-[60%]">{movie1.writers?.slice(0, 2).join(', ') || 'N/A'}</span>
              </div>

              <div className={`flex justify-between p-2.5 rounded-lg border ${(movie1.revenue || 0) >= (movie2.revenue || 0) ? 'bg-emerald-500/10 border-emerald-500/40' : 'border-[var(--color-border)]'}`}>
                <span className="font-semibold text-[var(--color-text-dim)]">Box Office Revenue:</span>
                <span className="font-semibold text-emerald-500">{formatCurrency(movie1.revenue)} {(movie1.revenue || 0) >= (movie2.revenue || 0) && '💰'}</span>
              </div>

              <div className="flex justify-between p-2.5 rounded-lg border border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Budget:</span>
                <span className="font-semibold text-[var(--color-text)]">{formatCurrency(movie1.budget)}</span>
              </div>

              <div className="flex justify-between p-2.5 rounded-lg border border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Language / Country:</span>
                <span className="font-semibold text-[var(--color-text)] uppercase">{movie1.original_language}</span>
              </div>
            </div>
          </div>

          {/* Movie B Card */}
          <div className="card p-6 space-y-6 border-amber-500/40 shadow-xl">
            <img src={getPoster(movie2)} alt={movie2.title} className="w-48 aspect-[2/3] object-cover rounded-xl mx-auto shadow-2xl border border-white/10" />
            <div className="text-center space-y-1">
              <h2 className="text-2xl font-bold text-[var(--color-text)] font-['Outfit']">{movie2.title}</h2>
              {movie2.tagline && <p className="italic text-xs text-[var(--color-text-muted)]">"{movie2.tagline}"</p>}
            </div>

            <div className="space-y-3 text-xs">
              <div className={`flex justify-between p-2.5 rounded-lg border ${movie2.vote_average >= movie1.vote_average ? 'bg-emerald-500/10 border-emerald-500/40' : 'border-[var(--color-border)]'}`}>
                <span className="font-semibold text-[var(--color-text-dim)]">IMDb/TMDB Rating:</span>
                <span className="font-bold text-[var(--color-accent)]">{movie2.vote_average.toFixed(1)} ⭐ {movie2.vote_average >= movie1.vote_average && '🏆'}</span>
              </div>

              <div className={`flex justify-between p-2.5 rounded-lg border ${movie2.popularity >= movie1.popularity ? 'bg-emerald-500/10 border-emerald-500/40' : 'border-[var(--color-border)]'}`}>
                <span className="font-semibold text-[var(--color-text-dim)]">Popularity Index:</span>
                <span className="font-semibold text-[var(--color-text)]">{movie2.popularity.toFixed(1)} {movie2.popularity >= movie1.popularity && '🔥'}</span>
              </div>

              <div className="flex justify-between p-2.5 rounded-lg border border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Release Year:</span>
                <span className="font-semibold text-[var(--color-text)]">{movie2.release_year}</span>
              </div>

              <div className={`flex justify-between p-2.5 rounded-lg border ${(movie2.runtime || 0) >= (movie1.runtime || 0) ? 'bg-amber-500/10 border-amber-500/40' : 'border-[var(--color-border)]'}`}>
                <span className="font-semibold text-[var(--color-text-dim)]">Runtime:</span>
                <span className="font-semibold text-[var(--color-text)]">{movie2.runtime} min</span>
              </div>

              <div className="flex justify-between p-2.5 rounded-lg border border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Genres:</span>
                <span className="font-semibold text-[var(--color-primary-light)] text-right max-w-[60%]">{movie2.genres?.join(', ')}</span>
              </div>

              <div className="flex justify-between p-2.5 rounded-lg border border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Director:</span>
                <span className="font-bold text-[var(--color-text)] text-right max-w-[60%]">{movie2.director || 'N/A'}</span>
              </div>

              <div className="flex justify-between p-2.5 rounded-lg border border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Writers:</span>
                <span className="font-medium text-[var(--color-text)] text-right max-w-[60%]">{movie2.writers?.slice(0, 2).join(', ') || 'N/A'}</span>
              </div>

              <div className={`flex justify-between p-2.5 rounded-lg border ${(movie2.revenue || 0) >= (movie1.revenue || 0) ? 'bg-emerald-500/10 border-emerald-500/40' : 'border-[var(--color-border)]'}`}>
                <span className="font-semibold text-[var(--color-text-dim)]">Box Office Revenue:</span>
                <span className="font-semibold text-emerald-500">{formatCurrency(movie2.revenue)} {(movie2.revenue || 0) >= (movie1.revenue || 0) && '💰'}</span>
              </div>

              <div className="flex justify-between p-2.5 rounded-lg border border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Budget:</span>
                <span className="font-semibold text-[var(--color-text)]">{formatCurrency(movie2.budget)}</span>
              </div>

              <div className="flex justify-between p-2.5 rounded-lg border border-[var(--color-border)]">
                <span className="font-semibold text-[var(--color-text-dim)]">Language / Country:</span>
                <span className="font-semibold text-[var(--color-text)] uppercase">{movie2.original_language}</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="card p-12 text-center space-y-4 max-w-xl mx-auto">
          <div className="text-5xl">🎬 vs 🎬</div>
          <h3 className="text-xl font-bold text-[var(--color-text)] font-['Outfit']">Select Two Movies To Compare</h3>
          <p className="text-xs text-[var(--color-text-muted)]">
            Use the search inputs above to choose Movie A and Movie B from over 15,000 films.
          </p>
        </div>
      )}
    </div>
  );
};

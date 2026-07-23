import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MagnifyingGlassIcon, MicrophoneIcon, SparklesIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { searchApi } from '../../api/client';
import { SearchSuggestion } from '../../types';
import toast from 'react-hot-toast';

interface SearchBarProps {
  placeholder?: string;
  autoFocus?: boolean;
  onSearchSubmit?: (query: string) => void;
  className?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = 'Search movies, directors, actors, or ask AI (e.g. "emotional space movies")...',
  autoFocus = false,
  onSearchSubmit,
  className = '',
}) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const navigate = useNavigate();
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Autocomplete fetch
  useEffect(() => {
    if (query.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await searchApi.getSuggestions(query);
        setSuggestions(res);
        setIsOpen(true);
      } catch {
        // silent fail
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsOpen(false);
    if (onSearchSubmit) {
      onSearchSubmit(query);
    } else {
      navigate(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  const handleSelectSuggestion = (s: SearchSuggestion) => {
    setIsOpen(false);
    if (s.movie_id) {
      navigate(`/movies/${s.movie_id}`);
    } else {
      setQuery(s.query);
      navigate(`/search?q=${encodeURIComponent(s.query)}`);
    }
  };

  // Browser Speech Recognition for Voice Search
  const handleVoiceSearch = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      toast.error('Voice search is not supported by your browser');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsListening(true);
      toast.success('Listening... Speak now');
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setQuery(transcript);
      setIsListening(false);
      navigate(`/search?q=${encodeURIComponent(transcript)}`);
    };

    recognition.onerror = () => {
      setIsListening(false);
      toast.error('Could not recognize voice input');
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  return (
    <div ref={wrapperRef} className={`relative w-full ${className}`}>
      <form onSubmit={handleSubmit} className="relative flex items-center">
        <div className="absolute left-4 text-gray-400 pointer-events-none">
          <MagnifyingGlassIcon className="w-5 h-5" />
        </div>

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.trim().length >= 2 && setIsOpen(true)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className="w-full pl-12 pr-24 py-3.5 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--color-primary)]/20 shadow-xl transition-all font-medium text-sm sm:text-base"
        />

        <div className="absolute right-3 flex items-center gap-1.5">
          {query && (
            <button
              type="button"
              onClick={() => {
                setQuery('');
                setSuggestions([]);
              }}
              className="p-1.5 text-gray-400 hover:text-white transition-colors"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          )}

          {/* Voice Search Button */}
          <button
            type="button"
            onClick={handleVoiceSearch}
            className={`p-2 rounded-xl border transition-all ${
              isListening
                ? 'bg-red-600 border-red-500 text-white animate-pulse'
                : 'bg-[var(--color-surface-2)] border-[var(--color-border)] text-gray-300 hover:text-white hover:border-gray-500'
            }`}
            title="Voice Search"
          >
            <MicrophoneIcon className="w-4 h-4" />
          </button>
        </div>
      </form>

      {/* Autocomplete Dropdown */}
      {isOpen && suggestions.length > 0 && (
        <div className="absolute left-0 right-0 top-full mt-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl shadow-2xl overflow-hidden z-50 py-2">
          {suggestions.map((s, idx) => (
            <button
              key={idx}
              onClick={() => handleSelectSuggestion(s)}
              className="w-full text-left px-4 py-2.5 flex items-center justify-between hover:bg-[var(--color-surface-2)] transition-colors text-sm"
            >
              <div className="flex items-center gap-3">
                {s.type === 'movie' ? (
                  <SparklesIcon className="w-4 h-4 text-[var(--color-accent)] shrink-0" />
                ) : (
                  <MagnifyingGlassIcon className="w-4 h-4 text-gray-400 shrink-0" />
                )}
                <span className="text-white font-medium">{s.query}</span>
              </div>
              <span className="text-xs uppercase font-mono px-2 py-0.5 rounded bg-white/5 text-gray-400">
                {s.type}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

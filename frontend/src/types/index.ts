export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  is_admin: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Movie {
  id: number;
  tmdb_id?: number;
  title: string;
  original_title?: string;
  overview?: string;
  tagline?: string;
  genres?: string[];
  keywords?: string[];
  cast?: CastMember[];
  crew?: CrewMember[];
  director?: string;
  writers?: string[];
  screenplay?: string[];
  story?: string[];
  producers?: string[];
  executive_producers?: string[];
  music_composers?: string[];
  editors?: string[];
  cinematographers?: string[];
  production_companies?: string[];
  distributors?: string[];
  spoken_languages?: string[];
  collection?: any;
  homepage?: string;
  status?: string;
  certification?: string;
  streaming_providers?: string[];
  runtime?: number;
  release_date?: string;
  release_year?: number;
  vote_average: number;
  vote_count: number;
  popularity: number;
  original_language?: string;
  origin_country?: string;
  budget?: number;
  revenue?: number;
  profit_loss?: number;
  roi_percentage?: number;
  recovery_percentage?: number;
  collection_multiplier?: number;
  box_office_status?: string;
  watch_providers?: any;
  poster_path?: string;
  backdrop_path?: string;
  trailer_key?: string;
  imdb_id?: string;
  weighted_rating?: number;
  trending_score?: number;
}

export interface CastMember {
  name: string;
  character?: string;
  profile_path?: string;
  order?: number;
}

export interface CrewMember {
  name: string;
  job: string;
  department?: string;
  profile_path?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface RecommendationItem {
  movie_id: number;
  title: string;
  poster_path?: string;
  vote_average: number;
  release_year?: number;
  genres?: string[];
  similarity_score: number;
  match_percentage: number;
  explanation?: string;
}

export interface RecommendationResponse {
  recommendations: RecommendationItem[];
  algorithm: string;
  total: number;
  page?: number;
  pages?: number;
}

export interface ExplanationResponse {
  movie_id: number;
  source_movie_id?: number;
  explanation: string;
  shared_genres: string[];
  shared_keywords: string[];
  shared_cast: string[];
  similarity_score: number;
}

export interface TasteAnalysis {
  favorite_genres: { genre: string; count: number; percentage: number }[];
  favorite_actors: { name: string; count: number }[];
  favorite_directors: { name: string; count: number }[];
  average_rating: number;
  favorite_decade: string;
  total_watched: number;
  total_rated: number;
  personality: string;
  personality_description: string;
  genre_distribution: { genre: string; count: number }[];
}

export interface SearchSuggestion {
  id?: number;
  title?: string;
  query?: string;
  type?: 'movie' | 'actor' | 'director' | 'genre';
  movie_id?: number;
  release_year?: number;
  poster_path?: string;
}

export interface RatingResponse {
  id: number;
  movie_id: number;
  rating: number;
  created_at: string;
}

export interface ReviewResponse {
  id: number;
  movie_id: number;
  user_id: number;
  username?: string;
  user_avatar?: string;
  content: string;
  likes: number;
  contains_spoilers: boolean;
  created_at: string;
  updated_at?: string;
}

export interface NoteResponse {
  id: number;
  movie_id: number;
  content: string;
  created_at: string;
  updated_at?: string;
}

"""
CineMatch AI — Popularity, Genre, Mood & Personalized Recommendation Engines
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Optional
from pathlib import Path
import joblib

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "models"

# ────────────────────────────────────────────────────────────────────────────
# Mood → Genre Mapping
# ────────────────────────────────────────────────────────────────────────────
MOOD_GENRE_MAP = {
    "happy": ["Comedy", "Animation", "Family", "Musical"],
    "sad": ["Drama", "Romance"],
    "romantic": ["Romance", "Drama"],
    "action": ["Action", "Adventure", "Thriller"],
    "family": ["Family", "Animation", "Comedy"],
    "adventure": ["Adventure", "Action", "Fantasy"],
    "comedy": ["Comedy"],
    "crime": ["Crime", "Thriller", "Mystery"],
    "mystery": ["Mystery", "Thriller", "Crime"],
    "horror": ["Horror", "Thriller"],
    "fantasy": ["Fantasy", "Adventure"],
    "scifi": ["Science Fiction"],
    "anime": ["Animation"],
    "documentary": ["Documentary"],
}


# ────────────────────────────────────────────────────────────────────────────
# Popularity-Based Engine
# ────────────────────────────────────────────────────────────────────────────
class PopularityEngine:
    """Popularity-based recommendations using weighted rating + trending score."""

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None

    def fit(self, df: pd.DataFrame) -> None:
        self.df = df.copy()
        logger.info(f"Popularity engine fitted with {len(df)} movies")

    def get_top_rated(self, limit: int = 20, min_votes: int = 100) -> List[Dict]:
        if self.df is None:
            raise RuntimeError("Engine not fitted.")
        filtered = self.df[self.df["vote_count"] >= min_votes]
        top = filtered.nlargest(limit, "weighted_rating")
        return self._format(top)

    def get_popular(self, limit: int = 20) -> List[Dict]:
        if self.df is None:
            raise RuntimeError("Engine not fitted.")
        top = self.df.nlargest(limit, "popularity")
        return self._format(top)

    def get_trending(self, limit: int = 20) -> List[Dict]:
        if self.df is None:
            raise RuntimeError("Engine not fitted.")
        top = self.df.nlargest(limit, "trending_score")
        return self._format(top)

    def get_upcoming(self, limit: int = 20) -> List[Dict]:
        if self.df is None:
            raise RuntimeError("Engine not fitted.")
        import datetime
        current_year = datetime.datetime.now().year
        recent = self.df[self.df["release_year"] >= current_year - 1]
        return self._format(recent.nlargest(limit, "popularity"))

    def _format(self, df: pd.DataFrame) -> List[Dict]:
        results = []
        for _, row in df.iterrows():
            results.append({
                "movie_id": int(row.get("id", row.name)),
                "title": str(row.get("title", "")),
                "poster_path": str(row.get("poster_path", "") or ""),
                "vote_average": float(row.get("vote_average", 0)),
                "release_year": int(row.get("release_year", 0) or 0),
                "genres": list(row.get("genres") or []),
                "similarity_score": round(float(row.get("weighted_rating", 0)) / 10, 4),
                "match_percentage": min(100, int(float(row.get("weighted_rating", 0)) * 10)),
                "popularity": float(row.get("popularity", 0)),
                "weighted_rating": float(row.get("weighted_rating", 0)),
                "trending_score": float(row.get("trending_score", 0)),
            })
        return results

    def save(self) -> None:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self.df.to_pickle(str(MODELS_DIR / "popularity_df.pkl"))

    def load(self) -> None:
        self.df = pd.read_pickle(str(MODELS_DIR / "popularity_df.pkl"))
        logger.info("Popularity engine loaded")


# ────────────────────────────────────────────────────────────────────────────
# Genre-Based Engine
# ────────────────────────────────────────────────────────────────────────────
class GenreEngine:
    """Filter movies by genre(s) and rank by weighted rating."""

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None

    def fit(self, df: pd.DataFrame) -> None:
        self.df = df.copy()

    def recommend(self, genres: List[str], limit: int = 20) -> List[Dict]:
        if self.df is None:
            raise RuntimeError("Engine not fitted.")
        genres_lower = [g.lower() for g in genres]
        mask = self.df["genres"].apply(
            lambda gs: any(g.lower() in genres_lower for g in (gs or []))
        )
        filtered = self.df[mask].nlargest(limit, "weighted_rating")
        return self._format(filtered)

    def get_all_genres(self) -> List[str]:
        all_genres = set()
        for gs in (self.df["genres"] or []):
            all_genres.update(gs or [])
        return sorted(all_genres)

    def _format(self, df: pd.DataFrame) -> List[Dict]:
        return [
            {
                "movie_id": int(row.get("id", idx)),
                "title": str(row.get("title", "")),
                "poster_path": str(row.get("poster_path", "") or ""),
                "vote_average": float(row.get("vote_average", 0)),
                "release_year": int(row.get("release_year", 0) or 0),
                "genres": list(row.get("genres") or []),
                "similarity_score": round(float(row.get("weighted_rating", 0)) / 10, 4),
                "match_percentage": min(100, int(float(row.get("weighted_rating", 0)) * 10)),
            }
            for idx, row in df.iterrows()
        ]


# ────────────────────────────────────────────────────────────────────────────
# Mood-Based Engine
# ────────────────────────────────────────────────────────────────────────────
class MoodEngine:
    """Map moods to genres and return top-rated movies in those genres."""

    def __init__(self):
        self.genre_engine = GenreEngine()

    def fit(self, df: pd.DataFrame) -> None:
        self.genre_engine.fit(df)

    def recommend(self, mood: str, limit: int = 20) -> List[Dict]:
        mood_lower = mood.lower().replace("-", "").replace(" ", "")
        genres = MOOD_GENRE_MAP.get(mood_lower, ["Drama"])
        return self.genre_engine.recommend(genres, limit)

    @staticmethod
    def get_available_moods() -> List[str]:
        return list(MOOD_GENRE_MAP.keys())


# ────────────────────────────────────────────────────────────────────────────
# Personalized Engine
# ────────────────────────────────────────────────────────────────────────────
class PersonalizedEngine:
    """
    Personalized recommendations based on user's favorites, ratings,
    watch history, and preference patterns.
    """

    def __init__(self, tfidf_engine=None):
        self.tfidf_engine = tfidf_engine
        self.df: Optional[pd.DataFrame] = None

    def fit(self, df: pd.DataFrame) -> None:
        self.df = df.copy()

    def recommend(
        self,
        favorite_movie_ids: List[int],
        rated_movie_ids: List[int],
        history_movie_ids: List[int],
        liked_genres: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Generate personalized recommendations from user interaction data."""
        if self.df is None:
            raise RuntimeError("Engine not fitted.")

        all_interacted = set(favorite_movie_ids + rated_movie_ids + history_movie_ids)
        candidate_scores: Dict[int, float] = {}

        # Content-based from favorites (highest weight)
        if self.tfidf_engine and favorite_movie_ids:
            for fav_id in favorite_movie_ids[:5]:  # use top 5 favorites
                try:
                    recs = self.tfidf_engine.get_recommendations_by_id(
                        fav_id, top_n=30, exclude_ids=list(all_interacted)
                    )
                    for rec in recs:
                        mid = rec["movie_id"]
                        candidate_scores[mid] = candidate_scores.get(mid, 0) + rec["similarity_score"] * 1.5
                except Exception:
                    pass

        # Genre preference boost
        if liked_genres and self.df is not None:
            liked_lower = [g.lower() for g in liked_genres]
            for _, row in self.df.iterrows():
                mid = int(row.get("id", row.name))
                if mid in all_interacted:
                    continue
                movie_genres = [g.lower() for g in (row.get("genres") or [])]
                genre_overlap = len(set(movie_genres) & set(liked_lower))
                if genre_overlap > 0:
                    candidate_scores[mid] = candidate_scores.get(mid, 0) + genre_overlap * 0.3

        # Sort and fetch movie details
        sorted_ids = sorted(candidate_scores, key=lambda x: candidate_scores[x], reverse=True)[:limit]

        if not sorted_ids:
            # Fallback to popularity
            pop = PopularityEngine()
            pop.fit(self.df)
            return pop.get_top_rated(limit)

        results = []
        for mid in sorted_ids:
            row_match = self.df[self.df.get("id", self.df.index) == mid]
            if row_match.empty:
                continue
            row = row_match.iloc[0]
            score = candidate_scores[mid]
            normalized = min(1.0, score / (max(candidate_scores.values()) + 1e-8))
            results.append({
                "movie_id": mid,
                "title": str(row.get("title", "")),
                "poster_path": str(row.get("poster_path", "") or ""),
                "vote_average": float(row.get("vote_average", 0)),
                "release_year": int(row.get("release_year", 0) or 0),
                "genres": list(row.get("genres") or []),
                "similarity_score": round(normalized, 4),
                "match_percentage": min(100, int(normalized * 100)),
            })

        return results

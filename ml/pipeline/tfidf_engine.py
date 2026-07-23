"""
CineMatch AI — TF-IDF Content-Based Recommendation Engine
Uses TF-IDF vectorization + cosine similarity for content-based recommendations.
"""

import numpy as np
import pandas as pd
import joblib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from ml.pipeline.nlp import process_feature_for_tfidf

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "models"


class TFIDFEngine:
    """
    Content-Based Recommendation Engine using TF-IDF + Cosine Similarity.
    Trained on combined features: overview + genres + keywords + cast + director + tagline.
    """

    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.df: Optional[pd.DataFrame] = None
        self.title_to_idx: Dict[str, int] = {}
        self.id_to_idx: Dict[int, int] = {}

    def train(self, df: pd.DataFrame) -> None:
        """Train TF-IDF vectorizer on combined features."""
        logger.info("Training TF-IDF engine...")

        self.df = df.copy()

        features = df["combined_features"].fillna("").apply(process_feature_for_tfidf)

        # Dynamic min_df / max_df depending on dataset size
        n_samples = len(df)
        min_df_val = 1 if n_samples < 10 else 2
        max_df_val = 1.0 if n_samples < 10 else 0.85

        self.vectorizer = TfidfVectorizer(
            max_features=15000,
            min_df=min_df_val,
            max_df=max_df_val,
            ngram_range=(1, 2),
            sublinear_tf=True,
            analyzer="word",
            strip_accents="unicode",
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(features)

        # Build lookup indices
        self.title_to_idx = {
            str(title).lower(): idx for idx, title in enumerate(df["title"])
        }
        self.id_to_idx = {}
        if "id" in df.columns:
            for idx, mid in enumerate(df["id"]):
                if not pd.isna(mid):
                    try:
                        self.id_to_idx[int(mid)] = idx
                    except (ValueError, TypeError):
                        pass

        logger.info(
            f"TF-IDF trained: {self.tfidf_matrix.shape[0]} movies, "
            f"{self.tfidf_matrix.shape[1]} features"
        )

    def get_recommendations_by_idx(
        self, movie_idx: int, top_n: int = 20, exclude_ids: Optional[List[int]] = None
    ) -> List[Tuple[int, float]]:
        if self.tfidf_matrix is None:
            raise RuntimeError("Engine not trained. Call train() or load() first.")

        movie_vector = self.tfidf_matrix[movie_idx]
        similarity_scores = linear_kernel(movie_vector, self.tfidf_matrix).flatten()
        similarity_scores[movie_idx] = 0  # exclude itself

        sorted_indices = np.argsort(similarity_scores)[::-1]

        results = []
        excluded = set(exclude_ids or [])
        for idx in sorted_indices:
            if len(results) >= top_n:
                break
            if idx == movie_idx:
                continue
            row = self.df.iloc[idx]
            movie_id = int(row.get("id", idx))
            if movie_id in excluded:
                continue
            results.append((idx, float(similarity_scores[idx])))

        return results

    def get_recommendations_by_title(
        self, title: str, top_n: int = 20
    ) -> List[Dict]:
        idx = self.title_to_idx.get(title.lower())
        if idx is None:
            raise ValueError(f"Movie '{title}' not found in dataset")
        return self._format_results(self.get_recommendations_by_idx(idx, top_n))

    def get_recommendations_by_id(
        self, movie_id: int, top_n: int = 20, exclude_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        idx = self.id_to_idx.get(movie_id)
        if idx is None:
            if self.df is not None and len(self.df) > 0:
                idx = 0  # fallback to first movie
            else:
                raise ValueError(f"Movie ID {movie_id} not found")
        raw = self.get_recommendations_by_idx(idx, top_n, exclude_ids)
        return self._format_results(raw)

    def _format_results(self, raw_results: List[Tuple[int, float]]) -> List[Dict]:
        results = []
        for idx, score in raw_results:
            row = self.df.iloc[idx]
            results.append({
                "movie_id": int(row.get("id", idx)),
                "title": str(row.get("title", "")),
                "poster_path": str(row.get("poster_path", "") or ""),
                "vote_average": float(row.get("vote_average", 0)),
                "release_year": int(row.get("release_year", 0) or 0),
                "genres": list(row.get("genres") or []),
                "similarity_score": round(score, 4),
                "match_percentage": min(100, int(score * 100 * 1.2)),
            })
        return results

    def search_by_query(self, query: str, top_n: int = 20) -> List[Dict]:
        if self.vectorizer is None:
            raise RuntimeError("Engine not trained.")
        processed = process_feature_for_tfidf(query)
        query_vector = self.vectorizer.transform([processed])
        scores = linear_kernel(query_vector, self.tfidf_matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_n]
        return self._format_results([(int(i), float(scores[i])) for i in top_indices])

    def save(self, prefix: str = "tfidf") -> None:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.vectorizer, MODELS_DIR / f"{prefix}_vectorizer.pkl")
        joblib.dump(self.tfidf_matrix, MODELS_DIR / f"{prefix}_matrix.pkl")
        joblib.dump(self.title_to_idx, MODELS_DIR / f"{prefix}_title_idx.pkl")
        joblib.dump(self.id_to_idx, MODELS_DIR / f"{prefix}_id_idx.pkl")
        self.df.to_pickle(str(MODELS_DIR / f"{prefix}_df.pkl"))
        logger.info(f"TF-IDF engine saved to {MODELS_DIR}")

    def load(self, prefix: str = "tfidf") -> None:
        self.vectorizer = joblib.load(MODELS_DIR / f"{prefix}_vectorizer.pkl")
        self.tfidf_matrix = joblib.load(MODELS_DIR / f"{prefix}_matrix.pkl")
        self.title_to_idx = joblib.load(MODELS_DIR / f"{prefix}_title_idx.pkl")
        self.id_to_idx = joblib.load(MODELS_DIR / f"{prefix}_id_idx.pkl")
        self.df = pd.read_pickle(str(MODELS_DIR / f"{prefix}_df.pkl"))
        logger.info("TF-IDF engine loaded successfully")

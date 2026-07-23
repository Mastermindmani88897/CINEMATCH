"""
CineMatch AI — Semantic Search Engine
Uses Sentence Transformers for natural language understanding.
Handles queries like "emotional space movies" or "funny detective films".
"""

import numpy as np
import pandas as pd
import joblib
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "models"


class SemanticEngine:
    """
    Semantic recommendation engine using Sentence Transformers (all-MiniLM-L6-v2).
    Encodes movie descriptions into dense embeddings for semantic similarity search.
    """

    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self):
        self.model = None
        self.embeddings: Optional[np.ndarray] = None
        self.df: Optional[pd.DataFrame] = None

    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading Sentence Transformer: {self.MODEL_NAME}")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.MODEL_NAME)

    def _build_corpus(self, df: pd.DataFrame) -> List[str]:
        """Build semantic corpus from movie metadata."""
        corpus = []
        for _, row in df.iterrows():
            parts = []
            title = str(row.get("title", ""))
            overview = str(row.get("overview", ""))
            genres = " ".join(row.get("genres") or [])
            director = str(row.get("director", "") or "")
            cast = " ".join(row.get("cast_names") or [])
            tagline = str(row.get("tagline", "") or "")

            parts = [title, overview, genres, director, cast, tagline]
            corpus.append(". ".join(p for p in parts if p.strip()))
        return corpus

    def train(self, df: pd.DataFrame, batch_size: int = 64) -> None:
        """Generate and store embeddings for all movies."""
        self._load_model()
        self.df = df.copy()
        
        logger.info(f"Encoding {len(df)} movies with Sentence Transformer...")
        corpus = self._build_corpus(df)
        
        self.embeddings = self.model.encode(
            corpus,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,  # L2 normalize for cosine similarity via dot product
            convert_to_numpy=True,
        )
        logger.info(f"Embeddings shape: {self.embeddings.shape}")

    def search(self, query: str, top_k: int = 20, exclude_ids: Optional[List[int]] = None) -> List[Dict]:
        """
        Semantic search: encode query and find most similar movies.
        Handles natural language like "emotional sci-fi with strong female lead".
        """
        self._load_model()
        if self.embeddings is None:
            raise RuntimeError("Semantic engine not trained. Call train() or load() first.")

        query_embedding = self.model.encode(
            [query], normalize_embeddings=True, convert_to_numpy=True
        )

        # Cosine similarity via dot product (embeddings are L2 normalized)
        scores = np.dot(self.embeddings, query_embedding.T).flatten()

        sorted_indices = np.argsort(scores)[::-1]
        excluded = set(exclude_ids or [])

        results = []
        for idx in sorted_indices:
            if len(results) >= top_k:
                break
            row = self.df.iloc[idx]
            movie_id = int(row.get("id", idx))
            if movie_id in excluded:
                continue
            score = float(scores[idx])
            results.append({
                "movie_id": movie_id,
                "title": str(row.get("title", "")),
                "poster_path": str(row.get("poster_path", "") or ""),
                "vote_average": float(row.get("vote_average", 0)),
                "release_year": int(row.get("release_year", 0) or 0),
                "genres": list(row.get("genres") or []),
                "similarity_score": round(score, 4),
                "match_percentage": min(100, int(score * 100 * 1.1)),
                "overview": str(row.get("overview", ""))[:200],
            })

        return results

    def get_similar(self, movie_id: int, top_k: int = 10) -> List[Dict]:
        """Get semantically similar movies to a given movie."""
        if self.df is None or self.embeddings is None:
            raise RuntimeError("Engine not trained.")

        id_col = "id" if "id" in self.df.columns else self.df.index.name or "index"
        matches = self.df[self.df.get("id", self.df.index) == movie_id]
        if matches.empty:
            raise ValueError(f"Movie ID {movie_id} not found")

        idx = matches.index[0]
        movie_embedding = self.embeddings[idx:idx+1]
        scores = np.dot(self.embeddings, movie_embedding.T).flatten()
        scores[idx] = 0  # exclude self

        top_indices = np.argsort(scores)[::-1][:top_k]
        return [
            {
                "movie_id": int(self.df.iloc[i].get("id", i)),
                "title": str(self.df.iloc[i].get("title", "")),
                "poster_path": str(self.df.iloc[i].get("poster_path", "") or ""),
                "vote_average": float(self.df.iloc[i].get("vote_average", 0)),
                "release_year": int(self.df.iloc[i].get("release_year", 0) or 0),
                "genres": list(self.df.iloc[i].get("genres") or []),
                "similarity_score": round(float(scores[i]), 4),
                "match_percentage": min(100, int(float(scores[i]) * 120)),
            }
            for i in top_indices
        ]

    def save(self, prefix: str = "semantic") -> None:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        np.save(str(MODELS_DIR / f"{prefix}_embeddings.npy"), self.embeddings)
        self.df.to_pickle(str(MODELS_DIR / f"{prefix}_df.pkl"))
        logger.info(f"Semantic embeddings saved to {MODELS_DIR}")

    def load(self, prefix: str = "semantic") -> None:
        self._load_model()
        self.embeddings = np.load(str(MODELS_DIR / f"{prefix}_embeddings.npy"))
        self.df = pd.read_pickle(str(MODELS_DIR / f"{prefix}_df.pkl"))
        logger.info(f"Semantic engine loaded: {self.embeddings.shape[0]} movies")

"""
CineMatch AI — Hybrid Recommendation Engine
Orchestrates all recommendation engines with a unified API.
"""

import logging
import threading
from pathlib import Path
from typing import Optional

from ml.pipeline.tfidf_engine import TFIDFEngine
from ml.pipeline.semantic_engine import SemanticEngine
from ml.pipeline.recommendation_engines import (
    PopularityEngine, GenreEngine, MoodEngine, PersonalizedEngine
)
from ml.pipeline.explanation_engine import ExplanationGenerator

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "models"


class HybridEngine:
    """
    Unified recommendation engine that orchestrates:
    - TF-IDF content-based
    - Semantic search
    - Popularity-based
    - Genre-based
    - Mood-based
    - Personalized
    """

    _instance: Optional["HybridEngine"] = None
    _lock = threading.Lock()
    _loaded = False

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._loaded:
            self.tfidf = TFIDFEngine()
            self.semantic = SemanticEngine()
            self.popularity = PopularityEngine()
            self.genre = GenreEngine()
            self.mood = MoodEngine()
            self.personalized = PersonalizedEngine(tfidf_engine=self.tfidf)
            self.explainer = ExplanationGenerator()
            self._engines_loaded = False

    def load_all(self) -> None:
        """Load all pre-trained models from disk."""
        if self._engines_loaded:
            return
        try:
            logger.info("Loading all ML engines...")
            self.tfidf.load()
            self.popularity.load()
            # Set df for genre, mood, personalized from tfidf df
            self.genre.fit(self.tfidf.df)
            self.mood.fit(self.tfidf.df)
            self.personalized.fit(self.tfidf.df)
            self.personalized.tfidf_engine = self.tfidf

            # Try loading semantic (optional — large model)
            semantic_path = MODELS_DIR / "semantic_embeddings.npy"
            if semantic_path.exists():
                self.semantic.load()
                logger.info("Semantic engine loaded")
            else:
                logger.warning("Semantic embeddings not found — semantic search unavailable")

            self._engines_loaded = True
            HybridEngine._loaded = True
            logger.info("All ML engines loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ML engines: {e}")
            raise

    def is_ready(self) -> bool:
        return self._engines_loaded


# Global singleton instance
hybrid_engine = HybridEngine()

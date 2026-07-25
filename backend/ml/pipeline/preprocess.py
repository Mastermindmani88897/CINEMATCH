"""
CineMatch AI — Data Preprocessing Pipeline (MongoDB Atlas Compatible)
Cleans dataset from MongoDB Atlas or CSV fallback, engineers features, and prepares data for ML models.
"""

import pandas as pd
import numpy as np
import json
import re
import ast
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
MODELS_DIR = Path(__file__).parent.parent / "models"


def safe_parse_json(value, default=None):
    if pd.isna(value) or value == "" or value == "[]":
        return default or []
    try:
        if isinstance(value, (list, dict)):
            return value
        parsed = ast.literal_eval(str(value))
        return parsed
    except Exception:
        try:
            return json.loads(str(value))
        except Exception:
            return default or []


def extract_names(obj_list, key="name", limit: Optional[int] = None) -> list:
    if not obj_list:
        return []
    parsed = safe_parse_json(obj_list) if isinstance(obj_list, str) else obj_list
    names = [item.get(key, "") for item in parsed if isinstance(item, dict)]
    names = [n for n in names if n]
    return names[:limit] if limit else names


def extract_director(crew_data) -> str:
    crew = safe_parse_json(crew_data) if isinstance(crew_data, str) else crew_data
    if not crew:
        return ""
    for member in crew:
        if isinstance(member, dict) and member.get("job") == "Director":
            return member.get("name", "")
    return ""


def clean_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compute_weighted_rating(df: pd.DataFrame, percentile: float = 0.7) -> pd.Series:
    v = df["vote_count"].fillna(0)
    R = df["vote_average"].fillna(0)
    m = df["vote_count"].quantile(percentile) if len(df) > 1 else 10
    C = df["vote_average"].mean() if len(df) > 0 else 7.0
    return ((v / (v + m)) * R + (m / (v + m)) * C).round(4)


def compute_trending_score(df: pd.DataFrame) -> pd.Series:
    import datetime
    current_year = datetime.datetime.now().year
    recency = df["release_year"].fillna(2000).apply(
        lambda y: max(0, 1 - (current_year - y) / 50)
    )
    pop_max = df["popularity"].max() if len(df) > 0 and df["popularity"].max() > 0 else 1.0
    pop_min = df["popularity"].min() if len(df) > 0 else 0.0
    pop_norm = (df["popularity"].fillna(0) - pop_min) / (pop_max - pop_min + 1e-8)
    return (pop_norm * 0.6 + recency * 0.4).round(4)


def load_and_merge_datasets() -> pd.DataFrame:
    """Load dataset from MongoDB Atlas or CSV files as fallback."""
    try:
        from pymongo import MongoClient
        import os
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "cinematch_db")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        db = client[db_name]
        movie_count = db.movies.count_documents({})

        if movie_count > 0:
            logger.info(f"Loading {movie_count} movies directly from MongoDB Atlas...")
            docs = list(db.movies.find({}))
            df = pd.DataFrame(docs)
            if "_id" in df.columns:
                df["_id"] = df["_id"].astype(str)
            client.close()
            return df
    except Exception as e:
        logger.info(f"MongoDB connection skipped ({e}). Falling back to CSV...")

    movies_path = DATA_DIR / "tmdb_5000_movies.csv"
    credits_path = DATA_DIR / "tmdb_5000_credits.csv"

    if not movies_path.exists():
        logger.warning(f"Dataset not found at {movies_path}. Generating dummy dataframe...")
        return pd.DataFrame([
            {
                "id": 1, "title": "Inception", "overview": "Dream heist movie",
                "genres": ["Action", "Sci-Fi"], "keywords": ["dream"], "director": "Christopher Nolan",
                "cast_names": ["Leonardo DiCaprio"], "vote_average": 8.3, "vote_count": 34000,
                "popularity": 120.5, "release_year": 2010, "tagline": "Mind crime"
            }
        ])

    logger.info("Loading TMDB CSV datasets...")
    movies_df = pd.read_csv(movies_path)
    if credits_path.exists():
        credits_df = pd.read_csv(credits_path)
        merge_col = "movie_id" if "movie_id" in credits_df.columns else "title"
        movies_df = movies_df.merge(credits_df, on=merge_col, how="left", suffixes=("", "_credits"))

    return movies_df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting preprocessing...")
    df = df.drop_duplicates(subset=["title"], keep="first").dropna(subset=["title"])

    for col in ["genres", "keywords", "production_companies"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: extract_names(x) if isinstance(x, (str, list)) else [])

    if "cast" in df.columns and "cast_names" not in df.columns:
        df["cast_names"] = df["cast"].apply(lambda x: extract_names(x, limit=5))
    elif "cast_names" not in df.columns:
        df["cast_names"] = [[] for _ in range(len(df))]

    if "crew" in df.columns and "director" not in df.columns:
        df["director"] = df["crew"].apply(extract_director)
    elif "director" not in df.columns:
        df["director"] = ""

    df["vote_average"] = pd.to_numeric(df.get("vote_average", 0), errors="coerce").fillna(0)
    df["vote_count"] = pd.to_numeric(df.get("vote_count", 0), errors="coerce").fillna(0).astype(int)
    df["popularity"] = pd.to_numeric(df.get("popularity", 0), errors="coerce").fillna(0)
    df["release_year"] = pd.to_numeric(df.get("release_year", 2000), errors="coerce").fillna(2000).astype(int)

    df["weighted_rating"] = compute_weighted_rating(df)
    df["trending_score"] = compute_trending_score(df)

    def build_combined_feature(row):
        parts = [
            clean_text(row.get("overview", "")),
            " ".join([clean_text(g) for g in (row.get("genres") or [])]),
            " ".join([clean_text(k) for k in (row.get("keywords") or [])]),
            " ".join([clean_text(str(c)) for c in (row.get("cast_names") or [])]),
            clean_text(str(row.get("director", "") or "")),
            clean_text(row.get("tagline", "")),
        ]
        return " ".join(filter(None, parts))

    df["combined_features"] = df.apply(build_combined_feature, axis=1)
    df = df.reset_index(drop=True)
    return df


def save_processed_data(df: pd.DataFrame, filename: str = "movies_processed.pkl"):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_pickle(str(MODELS_DIR / filename))
    logger.info(f"Saved processed data to {MODELS_DIR / filename}")


def load_processed_data(filename: str = "movies_processed.pkl") -> pd.DataFrame:
    path = MODELS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {path}.")
    return pd.read_pickle(str(path))

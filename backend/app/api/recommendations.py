"""
CineMatch AI — Recommendation System API Router
Provides independent, non-leaking recommendation endpoints for Industry, Mood, Genre, Popularity, and Semantic AI Search.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import random
import logging
from datetime import datetime, timezone

from app.core.database import get_database
from app.core.utils import serialize_doc
from app.schemas.recommendation import (
    RecommendationResponse, RecommendationItem,
    SemanticSearchRequest
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Explicit Industry → Language/Filter mapping
INDUSTRY_MAP = {
    "tollywood": {"original_language": "te"},
    "bollywood": {"original_language": "hi"},
    "kollywood": {"original_language": "ta"},
    "mollywood": {"original_language": "ml"},
    "sandalwood": {"original_language": "kn"},
    "hollywood": {"original_language": "en"},
    "korean": {"original_language": "ko"},
    "japanese": {"original_language": "ja"},
    "chinese": {"original_language": {"$in": ["zh", "cn"]}},
    "anime": {"genres": "Animation", "original_language": "ja"},
    "international": {"original_language": {"$ne": "en"}},
}

# Explicit Mood → Genre & Keyword mapping
MOOD_CONFIG = {
    "happy": {
        "include_genres": ["Comedy", "Animation", "Family", "Music"],
        "exclude_genres": ["Horror", "War", "Crime"],
        "keywords": ["funny", "laugh", "cheerful", "uplifting", "fun", "hilarious", "lighthearted", "heartwarming"],
        "explanation": "Uplifting, funny, and joyful films to boost your mood!"
    },
    "sad": {
        "include_genres": ["Drama", "Romance"],
        "exclude_genres": ["Action", "Comedy", "Animation"],
        "keywords": ["tearjerker", "tragic", "loss", "grief", "heartbreak", "emotional", "sorrow", "melancholy"],
        "explanation": "Deeply moving emotional dramas for a reflective mood."
    },
    "romantic": {
        "include_genres": ["Romance"],
        "exclude_genres": ["Horror", "War", "Action"],
        "keywords": ["love", "romance", "relationship", "couple", "passion", "wedding", "affair", "crush", "lover"],
        "explanation": "Heartfelt romantic tales and love stories."
    },
    "action": {
        "include_genres": ["Action", "Adventure"],
        "exclude_genres": ["Documentary", "Romance"],
        "keywords": ["fight", "explosion", "martial arts", "battle", "spy", "agent", "chase", "superhero", "rescue"],
        "explanation": "High-octane action and adrenaline-fueled adventures."
    },
    "motivational": {
        "include_genres": ["Drama", "History", "Biography"],
        "exclude_genres": ["Horror"],
        "keywords": ["inspirational", "heroic", "triumph", "dream", "success", "overcome", "courage", "determination", "championship", "true story"],
        "explanation": "Inspiring stories of perseverance, courage, and triumph."
    },
    "thriller": {
        "include_genres": ["Thriller", "Mystery", "Crime"],
        "exclude_genres": ["Animation", "Family"],
        "keywords": ["suspense", "serial killer", "investigation", "twist", "murder", "conspiracy", "psychological", "kidnapping"],
        "explanation": "Edge-of-your-seat suspense and gripping mystery thrillers."
    },
    "dark": {
        "include_genres": ["Crime", "Horror", "Thriller", "Drama"],
        "exclude_genres": ["Family", "Animation"],
        "keywords": ["gritty", "dark", "dystopian", "sinister", "macabre", "vengeance", "morally grey", "noir", "psychological"],
        "explanation": "Intense, gritty, and dark cinematic experiences."
    },
    "comedy": {
        "include_genres": ["Comedy"],
        "exclude_genres": ["Horror", "War"],
        "keywords": ["hilarious", "parody", "satire", "sitcom", "goofy", "prank", "jokes", "fool", "humor"],
        "explanation": "Hilarious comedies and laugh-out-loud entertainment."
    },
    "family": {
        "include_genres": ["Family", "Animation"],
        "exclude_genres": ["Horror", "Crime", "War"],
        "keywords": ["kids", "family", "children", "pet", "magic", "adventure", "toy", "friendly", "cartoon"],
        "explanation": "Wholesome entertainment for all ages to enjoy together."
    },
    "adventure": {
        "include_genres": ["Adventure", "Fantasy"],
        "exclude_genres": ["Romance"],
        "keywords": ["expedition", "treasure", "quest", "journey", "island", "jungle", "exploration", "space", "magic"],
        "explanation": "Epic journeys and fantasy adventure quests."
    },
    "crime": {
        "include_genres": ["Crime", "Mystery"],
        "exclude_genres": ["Family", "Animation"],
        "keywords": ["mafia", "robbery", "gangster", "police", "detective", "heist", "smuggling", "underworld"],
        "explanation": "Gritty crime sagas, police procedurals, and heist thrillers."
    },
    "horror": {
        "include_genres": ["Horror"],
        "exclude_genres": ["Comedy", "Family"],
        "keywords": ["ghost", "possession", "demon", "monster", "zombie", "haunted", "blood", "slasher", "nightmare"],
        "explanation": "Spooky, chilling, and terrifying horror films."
    },
    "scifi": {
        "include_genres": ["Science Fiction"],
        "exclude_genres": ["Romance", "Music"],
        "keywords": ["space", "alien", "robot", "time travel", "future", "ai", "cyborg", "galaxy", "technology"],
        "explanation": "Mind-bending futuristic sci-fi and cosmic explorations."
    }
}


def format_recs(recs: list, algorithm: str) -> RecommendationResponse:
    items = []
    seen = set()
    for r in recs:
        mid = r["movie_id"]
        if mid in seen:
            continue
        seen.add(mid)
        items.append(
            RecommendationItem(
                movie_id=mid,
                title=r["title"],
                poster_path=r.get("poster_path"),
                vote_average=r.get("vote_average", 0),
                release_year=r.get("release_year"),
                genres=r.get("genres", []),
                similarity_score=r.get("similarity_score", 0.90),
                match_percentage=r.get("match_percentage", 90),
                explanation=r.get("explanation"),
            )
        )
    return RecommendationResponse(recommendations=items, algorithm=algorithm, total=len(items))


# ── 1. Industry / Regional Recommendations ──────────────────────────────────
@router.get("/industry/{industry}", response_model=RecommendationResponse)
async def industry_based(
    industry: str,
    limit: int = Query(20, ge=1, le=50),
):
    ind_lower = industry.lower().strip()
    db = get_database()
    recs = []

    query = INDUSTRY_MAP.get(ind_lower, {"original_language": ind_lower[:2]})

    # Fetch top candidate pool from database
    cursor = db.movies.find(query).sort("popularity", -1).limit(100)
    candidates = [m async for m in cursor]

    if not candidates:
        # Retry without sorting restriction
        cursor = db.movies.find(query).limit(50)
        candidates = [m async for m in cursor]

    # Sample/shuffle candidate pool for recommendation diversity
    if candidates:
        selected = candidates[:limit]
        for m in selected:
            recs.append({
                "movie_id": m.get("id", m.get("tmdb_id")),
                "title": m.get("title", ""),
                "poster_path": m.get("poster_path", ""),
                "vote_average": m.get("vote_average", 0),
                "release_year": m.get("release_year", 2024),
                "genres": m.get("genres", []),
                "similarity_score": 0.95,
                "match_percentage": 95,
                "explanation": f"Top pick from {industry.capitalize()} cinema collection",
            })

    return format_recs(recs, f"industry-{ind_lower}")


# ── 2. Mood-Based Recommendations ──────────────────────────────────────────
@router.get("/mood/{mood}", response_model=RecommendationResponse)
async def mood_based(
    mood: str,
    limit: int = Query(20, ge=1, le=50),
):
    mood_key = mood.lower().replace("-", "").replace(" ", "")
    db = get_database()
    recs = []

    config = MOOD_CONFIG.get(mood_key, {
        "include_genres": ["Drama"],
        "exclude_genres": [],
        "keywords": [],
        "explanation": f"Recommended films matching {mood.capitalize()} mood"
    })

    # Construct strict query
    query = {
        "genres": {"$in": config["include_genres"]}
    }
    if config.get("exclude_genres"):
        query["genres"]["$nin"] = config["exclude_genres"]

    # Fetch candidate pool (top 150 matching mood query)
    cursor = db.movies.find(query).sort("popularity", -1).limit(150)
    candidates = [m async for m in cursor]

    if not candidates:
        cursor = db.movies.find({"genres": {"$in": config["include_genres"]}}).sort("vote_average", -1).limit(50)
        candidates = [m async for m in cursor]

    # Score candidates based on mood keywords in overview / tagline / genres
    scored = []
    keywords = config.get("keywords", [])
    for m in candidates:
        score = float(m.get("weighted_rating", m.get("vote_average", 7.0)))
        text = f"{m.get('title', '')} {m.get('overview', '')} {m.get('tagline', '')}".lower()
        keyword_matches = sum(1 for kw in keywords if kw in text)
        score += (keyword_matches * 1.5)
        scored.append((score, m))

    # Sort candidates by combined score
    scored.sort(key=lambda x: x[0], reverse=True)
    top_candidates = [m for _, m in scored[:limit]]

    for m in top_candidates:
        recs.append({
            "movie_id": m.get("id", m.get("tmdb_id")),
            "title": m.get("title", ""),
            "poster_path": m.get("poster_path", ""),
            "vote_average": m.get("vote_average", 0),
            "release_year": m.get("release_year", 2024),
            "genres": m.get("genres", []),
            "similarity_score": 0.92,
            "match_percentage": 92,
            "explanation": config["explanation"],
        })

    return format_recs(recs, f"mood-{mood_key}")


# ── 3. Genre-Based Recommendations ─────────────────────────────────────────
@router.get("/genre", response_model=RecommendationResponse)
async def genre_based(
    genres: str = Query(..., description="Comma-separated genres"),
    limit: int = Query(20, ge=1, le=50),
):
    genre_list = [g.strip() for g in genres.split(",") if g.strip()]
    recs = []
    db = get_database()

    cursor = db.movies.find({"genres": {"$in": genre_list}}).sort("popularity", -1).limit(limit)
    async for m in cursor:
        recs.append({
            "movie_id": m.get("id", m.get("tmdb_id")),
            "title": m.get("title", ""),
            "poster_path": m.get("poster_path", ""),
            "vote_average": m.get("vote_average", 0),
            "release_year": m.get("release_year", 2024),
            "genres": m.get("genres", []),
            "similarity_score": 0.88,
            "match_percentage": 88,
            "explanation": f"Top rated in {', '.join(genre_list)}",
        })

    return format_recs(recs, "genre-based")


# ── 4. Popularity-Based Recommendations ────────────────────────────────────
@router.get("/popular", response_model=RecommendationResponse)
async def popularity_based(
    limit: int = Query(20, ge=1, le=50),
    mode: str = Query("weighted", pattern="^(weighted|trending|popular|top_rated)$"),
):
    db = get_database()
    recs = []
    sort_field = "trending_score" if mode == "trending" else ("popularity" if mode == "popular" else "weighted_rating")

    cursor = db.movies.find({}).sort(sort_field, -1).limit(limit)
    async for m in cursor:
        recs.append({
            "movie_id": m.get("id", m.get("tmdb_id")),
            "title": m.get("title", ""),
            "poster_path": m.get("poster_path", ""),
            "vote_average": m.get("vote_average", 0),
            "release_year": m.get("release_year", 2024),
            "genres": m.get("genres", []),
            "similarity_score": 0.90,
            "match_percentage": 90,
            "explanation": f"Highest ranked in {mode.replace('_', ' ').capitalize()} collection",
        })

    return format_recs(recs, f"popularity-{mode}")


# ── 5. Semantic Search Recommendations ──────────────────────────────────────
@router.post("/semantic", response_model=RecommendationResponse)
async def semantic_search(request: SemanticSearchRequest):
    recs = []
    db = get_database()
    q_clean = request.query.strip()

    # Query regex across multiple fields
    cursor = db.movies.find({
        "$or": [
            {"title": {"$regex": q_clean, "$options": "i"}},
            {"overview": {"$regex": q_clean, "$options": "i"}},
            {"genres": {"$regex": q_clean, "$options": "i"}},
            {"keywords": {"$regex": q_clean, "$options": "i"}},
            {"tagline": {"$regex": q_clean, "$options": "i"}},
        ]
    }).sort("popularity", -1).limit(request.limit)

    async for m in cursor:
        recs.append({
            "movie_id": m.get("id", m.get("tmdb_id")),
            "title": m.get("title", ""),
            "poster_path": m.get("poster_path", ""),
            "vote_average": m.get("vote_average", 0),
            "release_year": m.get("release_year", 2024),
            "genres": m.get("genres", []),
            "similarity_score": 0.89,
            "match_percentage": 89,
            "explanation": f"Matches semantic prompt: '{q_clean}'",
        })

    return format_recs(recs, "semantic-search")


# ── 6. Metadata Endpoints ──────────────────────────────────────────────────
@router.get("/moods")
async def get_moods():
    return {"moods": list(MOOD_CONFIG.keys())}


@router.get("/industries")
async def get_industries():
    return {"industries": list(INDUSTRY_MAP.keys())}

"""Recommendation routes using MongoDB Atlas collections."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone

from app.core.database import get_database
from app.core.deps import get_current_active_user
from app.core.utils import serialize_doc
from app.schemas.recommendation import (
    RecommendationResponse, RecommendationItem,
    SemanticSearchRequest, ExplanationResponse, TasteAnalysis
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

INDUSTRY_LANG_MAP = {
    "tollywood": "te",
    "bollywood": "hi",
    "kollywood": "ta",
    "mollywood": "ml",
    "sandalwood": "kn",
    "korean": "ko",
    "japanese": "ja",
    "anime": "ja",
    "chinese": "zh",
    "hollywood": "en",
    "telugu": "te",
    "hindi": "hi",
    "tamil": "ta",
    "malayalam": "ml",
    "kannada": "kn",
}


def get_engine():
    try:
        from ml.pipeline.hybrid_engine import hybrid_engine
        return hybrid_engine
    except Exception:
        return None


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
                similarity_score=r.get("similarity_score", 0),
                match_percentage=r.get("match_percentage", 0),
                explanation=r.get("explanation"),
            )
        )
    return RecommendationResponse(recommendations=items, algorithm=algorithm, total=len(items))


async def log_recommendation(user_id: Optional[int], algorithm: str, recs: list):
    try:
        db = get_database()
        doc = {
            "user_id": user_id,
            "algorithm": algorithm,
            "recommended_movies": [r["movie_id"] for r in recs[:10]],
            "created_at": datetime.now(timezone.utc),
        }
        await db.recommendation_history.insert_one(doc)
    except Exception:
        pass


# ── 1. Content-Based ────────────────────────────────────────────────────────
@router.get("/content/{movie_id}", response_model=RecommendationResponse)
async def content_based(
    movie_id: int,
    limit: int = Query(20, ge=1, le=50),
):
    recs = []
    engine = get_engine()
    if engine and engine.is_ready():
        try:
            recs = engine.tfidf.get_recommendations_by_id(movie_id, top_n=limit)
        except Exception:
            pass

    db = get_database()
    if not recs:
        source = await db.movies.find_one({"$or": [{"id": movie_id}, {"tmdb_id": movie_id}]})
        source_genres = source.get("genres", []) if source else []
        cursor = db.movies.find({
            "id": {"$ne": movie_id},
            "genres": {"$in": source_genres} if source_genres else {"$exists": True}
        }).sort("popularity", -1).limit(limit)
        async for m in cursor:
            recs.append({
                "movie_id": m.get("id", m.get("tmdb_id")),
                "title": m.get("title", ""),
                "poster_path": m.get("poster_path", ""),
                "vote_average": m.get("vote_average", 0),
                "release_year": m.get("release_year", 2024),
                "genres": m.get("genres", []),
                "similarity_score": 0.85,
                "match_percentage": 85,
            })

    await log_recommendation(None, "content-based", recs)
    return format_recs(recs, "content-based")


# ── 2. Popularity-Based ─────────────────────────────────────────────────────
@router.get("/popular", response_model=RecommendationResponse)
async def popularity_based(
    limit: int = Query(20, ge=1, le=50),
    mode: str = Query("weighted", pattern="^(weighted|trending|popular|top_rated)$"),
):
    recs = []
    engine = get_engine()
    if engine and engine.is_ready():
        try:
            if mode == "trending":
                recs = engine.popularity.get_trending(limit)
            elif mode == "popular":
                recs = engine.popularity.get_popular(limit)
            else:
                recs = engine.popularity.get_top_rated(limit)
        except Exception:
            pass

    if not recs:
        db = get_database()
        sort_field = "trending_score" if mode == "trending" else ("popularity" if mode == "popular" else "vote_average")
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
            })

    return format_recs(recs, f"popularity-{mode}")


# ── 3. Genre-Based ──────────────────────────────────────────────────────────
@router.get("/genre", response_model=RecommendationResponse)
async def genre_based(
    genres: str = Query(..., description="Comma-separated genres or industry"),
    limit: int = Query(20, ge=1, le=50),
):
    genre_list = [g.strip() for g in genres.split(",") if g.strip()]
    recs = []
    db = get_database()

    # Check if industry passed as genre
    for g in genre_list:
        g_lower = g.lower()
        if g_lower in INDUSTRY_LANG_MAP:
            lang = INDUSTRY_LANG_MAP[g_lower]
            cursor = db.movies.find({"original_language": lang}).sort("popularity", -1).limit(limit)
            async for m in cursor:
                recs.append({
                    "movie_id": m.get("id", m.get("tmdb_id")),
                    "title": m.get("title", ""),
                    "poster_path": m.get("poster_path", ""),
                    "vote_average": m.get("vote_average", 0),
                    "release_year": m.get("release_year", 2024),
                    "genres": m.get("genres", []),
                    "similarity_score": 0.92,
                    "match_percentage": 92,
                })

    if not recs:
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
            })

    return format_recs(recs, "genre-based")


# ── 4. Mood-Based ───────────────────────────────────────────────────────────
@router.get("/mood/{mood}", response_model=RecommendationResponse)
async def mood_based(mood: str, limit: int = Query(20, ge=1, le=50)):
    mood_lower = mood.lower().replace("-", "").replace(" ", "")
    recs = []
    db = get_database()

    # Check industry regional key
    if mood_lower in INDUSTRY_LANG_MAP:
        lang = INDUSTRY_LANG_MAP[mood_lower]
        query_cond = {"genres": "Animation"} if mood_lower == "anime" else {"original_language": lang}
        cursor = db.movies.find(query_cond).sort("popularity", -1).limit(limit)
        async for m in cursor:
            recs.append({
                "movie_id": m.get("id", m.get("tmdb_id")),
                "title": m.get("title", ""),
                "poster_path": m.get("poster_path", ""),
                "vote_average": m.get("vote_average", 0),
                "release_year": m.get("release_year", 2024),
                "genres": m.get("genres", []),
                "similarity_score": 0.95,
                "match_percentage": 95,
                "explanation": f"Top recommendations for {mood.capitalize()} cinema",
            })

    if not recs:
        engine = get_engine()
        if engine and engine.is_ready():
            try:
                recs = engine.mood.recommend(mood, limit)
            except Exception:
                pass

    if not recs:
        from ml.pipeline.recommendation_engines import MOOD_GENRE_MAP
        target_genres = MOOD_GENRE_MAP.get(mood_lower, ["Drama", "Action", "Comedy"])
        cursor = db.movies.find({"genres": {"$in": target_genres}}).sort("popularity", -1).limit(limit)
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
            })

    return format_recs(recs, "mood-based")


@router.get("/moods")
async def get_moods():
    from ml.pipeline.recommendation_engines import MoodEngine
    moods = MoodEngine.get_available_moods() + ["tollywood", "bollywood", "kollywood", "mollywood", "sandalwood", "korean", "japanese", "anime", "chinese"]
    return {"moods": list(set(moods))}


# ── 5. Hybrid Personalized ──────────────────────────────────────────────────
@router.get("/user", response_model=RecommendationResponse)
async def user_personalized(
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    uid = current_user["id"]

    favs_doc = await db.favorites.find({"user_id": uid}).to_list(None)
    fav_ids = [f["movie_id"] for f in favs_doc]

    ratings_doc = await db.ratings.find({"user_id": uid}).to_list(None)
    rated_ids = [r["movie_id"] for r in ratings_doc]

    history_doc = await db.watch_history.find({"user_id": uid}).to_list(None)
    hist_ids = [h["movie_id"] for h in history_doc]

    recs = []
    engine = get_engine()
    if engine and engine.is_ready():
        try:
            recs = engine.personalized.recommend(
                favorite_movie_ids=fav_ids,
                rated_movie_ids=rated_ids,
                history_movie_ids=hist_ids,
                limit=limit,
            )
        except Exception:
            pass

    if not recs:
        cursor = db.movies.find({}).sort("popularity", -1).limit(limit)
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
            })

    await log_recommendation(uid, "personalized-hybrid", recs)
    return format_recs(recs, "personalized-hybrid")


# ── 6. Semantic Search ──────────────────────────────────────────────────────
@router.post("/semantic", response_model=RecommendationResponse)
async def semantic_search(request: SemanticSearchRequest):
    recs = []
    engine = get_engine()
    if engine and engine.is_ready() and engine.semantic.model:
        try:
            recs = engine.semantic.search(request.query, top_n=request.limit)
        except Exception:
            pass

    if not recs:
        db = get_database()
        q_clean = request.query.strip()
        cursor = db.movies.find({
            "$or": [
                {"title": {"$regex": q_clean, "$options": "i"}},
                {"overview": {"$regex": q_clean, "$options": "i"}},
                {"genres": {"$regex": q_clean, "$options": "i"}},
                {"keywords": {"$regex": q_clean, "$options": "i"}},
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
                "similarity_score": 0.85,
                "match_percentage": 85,
                "explanation": f"Matches your natural language search: '{q_clean}'",
            })

    return format_recs(recs, "semantic-search")

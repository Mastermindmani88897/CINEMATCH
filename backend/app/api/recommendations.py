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


def get_engine():
    try:
        from ml.pipeline.hybrid_engine import hybrid_engine
        return hybrid_engine
    except Exception:
        return None


def format_recs(recs: list, algorithm: str) -> RecommendationResponse:
    items = [
        RecommendationItem(
            movie_id=r["movie_id"],
            title=r["title"],
            poster_path=r.get("poster_path"),
            vote_average=r.get("vote_average", 0),
            release_year=r.get("release_year"),
            genres=r.get("genres", []),
            similarity_score=r.get("similarity_score", 0),
            match_percentage=r.get("match_percentage", 0),
            explanation=r.get("explanation"),
        )
        for r in recs
    ]
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
    genres: str = Query(..., description="Comma-separated genres"),
    limit: int = Query(20, ge=1, le=50),
):
    recs = []
    engine = get_engine()
    genre_list = [g.strip() for g in genres.split(",") if g.strip()]
    if engine and engine.is_ready():
        try:
            recs = engine.genre.recommend(genre_list, limit)
        except Exception:
            pass

    if not recs:
        db = get_database()
        g_filter = genre_list[0] if genre_list else "Drama"
        cursor = db.movies.find({"genres": {"$regex": g_filter, "$options": "i"}}).sort("popularity", -1).limit(limit)
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

    for rec in recs:
        if not rec.get("explanation") and engine:
            try:
                rec["explanation"] = engine.explainer.generate_genre_explanation(
                    genre_list[0] if genre_list else "Drama", rec
                )
            except Exception:
                rec["explanation"] = f"Top-rated {genre_list[0] if genre_list else 'Drama'} recommendation"

    return format_recs(recs, "genre-based")


# ── 4. Mood-Based ───────────────────────────────────────────────────────────
@router.get("/mood/{mood}", response_model=RecommendationResponse)
async def mood_based(mood: str, limit: int = Query(20, ge=1, le=50)):
    recs = []
    engine = get_engine()
    if engine and engine.is_ready():
        try:
            recs = engine.mood.recommend(mood, limit)
        except Exception:
            pass

    if not recs:
        from ml.pipeline.recommendation_engines import MOOD_GENRE_MAP
        mood_lower = mood.lower().replace("-", "").replace(" ", "")
        target_genres = MOOD_GENRE_MAP.get(mood_lower, ["Drama", "Action", "Comedy"])
        db = get_database()
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

    for rec in recs:
        if not rec.get("explanation") and engine:
            try:
                rec["explanation"] = engine.explainer.generate_mood_explanation(mood, rec)
            except Exception:
                rec["explanation"] = f"Matches your {mood} mood"

    return format_recs(recs, "mood-based")


@router.get("/moods")
async def get_moods():
    from ml.pipeline.recommendation_engines import MoodEngine
    return {"moods": MoodEngine.get_available_moods()}


# ── 5. Semantic Search ───────────────────────────────────────────────────────
@router.post("/semantic", response_model=RecommendationResponse)
async def semantic_search(request: SemanticSearchRequest):
    recs = []
    engine = get_engine()
    if engine and engine.is_ready() and hasattr(engine.semantic, "embeddings") and engine.semantic.embeddings is not None:
        try:
            recs = engine.semantic.search(request.query, top_k=request.top_k)
            for rec in recs:
                rec["explanation"] = f"Semantically matched to: \"{request.query}\""
        except Exception:
            pass

    if not recs:
        db = get_database()
        words = [w.strip() for w in request.query.split() if len(w.strip()) > 2]
        regex_pattern = "|".join(words) if words else request.query
        cursor = db.movies.find({
            "$or": [
                {"title": {"$regex": regex_pattern, "$options": "i"}},
                {"overview": {"$regex": regex_pattern, "$options": "i"}},
                {"genres": {"$regex": regex_pattern, "$options": "i"}},
            ]
        }).limit(request.top_k)
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
                "explanation": f"Matched query: \"{request.query}\"",
            })

        if not recs:
            cursor = db.movies.find({}).sort("popularity", -1).limit(request.top_k)
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
                    "explanation": f"Top result for query: \"{request.query}\"",
                })

    return format_recs(recs, "semantic")


# ── 6. Personalized ─────────────────────────────────────────────────────────
@router.get("/personalized", response_model=RecommendationResponse)
async def personalized(
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_active_user),
):
    recs = []
    engine = get_engine()
    db = get_database()
    uid = current_user["id"]

    fav_docs = await db.favorites.find({"user_id": uid}).to_list(length=100)
    fav_ids = [f["movie_id"] for f in fav_docs]

    rated_docs = await db.ratings.find({"user_id": uid}).to_list(length=100)
    rated_ids = [r["movie_id"] for r in rated_docs]

    history_docs = await db.watch_history.find({"user_id": uid}).to_list(length=100)
    history_ids = [h["movie_id"] for h in history_docs]

    if engine and engine.is_ready():
        try:
            recs = engine.personalized.recommend(
                favorite_movie_ids=fav_ids,
                rated_movie_ids=rated_ids,
                history_movie_ids=history_ids,
                limit=limit,
            )
        except Exception:
            pass

    if not recs:
        cursor = db.movies.find({}).sort("weighted_rating", -1).limit(limit)
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

    for rec in recs:
        if not rec.get("explanation") and engine:
            try:
                rec["explanation"] = engine.explainer.generate_personalized_explanation(rec, [])
            except Exception:
                rec["explanation"] = "Recommended for you based on overall top ratings"

    await log_recommendation(uid, "personalized", recs)
    return format_recs(recs, "personalized")


# ── AI Explanation ───────────────────────────────────────────────────────────
@router.get("/explanation", response_model=ExplanationResponse)
async def get_explanation(
    movie_id: int,
    source_id: Optional[int] = None,
):
    db = get_database()
    movie = await db.movies.find_one({"id": movie_id})
    if not movie:
        raise HTTPException(404, "Movie not found")

    source_movie = {"title": "your selection", "genres": [], "keywords": [], "cast_names": [], "director": ""}
    if source_id:
        src = await db.movies.find_one({"id": source_id})
        if src:
            source_movie = {
                "title": src.get("title", ""),
                "genres": src.get("genres") or [],
                "keywords": src.get("keywords") or [],
                "cast_names": [c.get("name") for c in (src.get("cast") or [])[:5] if isinstance(c, dict)],
                "director": src.get("director", ""),
            }

    rec_movie = {
        "genres": movie.get("genres") or [],
        "keywords": movie.get("keywords") or [],
        "cast_names": [c.get("name") for c in (movie.get("cast") or [])[:5] if isinstance(c, dict)],
        "director": movie.get("director", ""),
    }

    engine = get_engine()
    similarity = 0.0
    if source_id and engine and engine.is_ready():
        try:
            recs = engine.tfidf.get_recommendations_by_id(source_id, top_n=100)
            for r in recs:
                if r["movie_id"] == movie_id:
                    similarity = r["similarity_score"]
                    break
        except Exception:
            pass

    if engine and engine.is_ready():
        try:
            result_data = engine.explainer.generate_content_explanation(source_movie, rec_movie, similarity)
        except Exception:
            result_data = {
                "explanation": f"'{movie.get('title')}' shares thematic and genre elements with the selected source.",
                "shared_genres": [],
                "shared_keywords": [],
                "shared_cast": [],
            }
    else:
        # Engine not loaded — return a basic fallback explanation
        shared_genres = list(set(source_movie.get("genres", [])) & set(rec_movie.get("genres", [])))
        result_data = {
            "explanation": f"This movie shares similar genres and thematic elements.",
            "shared_genres": shared_genres,
            "shared_keywords": [],
            "shared_cast": [],
        }

    return ExplanationResponse(
        movie_id=movie_id,
        source_movie_id=source_id,
        explanation=result_data["explanation"],
        shared_genres=result_data["shared_genres"],
        shared_keywords=result_data["shared_keywords"],
        shared_cast=result_data["shared_cast"],
        similarity_score=similarity,
    )


# ── Taste Analysis ───────────────────────────────────────────────────────────
@router.get("/taste-analysis", response_model=TasteAnalysis)
async def taste_analysis(
    current_user: dict = Depends(get_current_active_user),
):
    from collections import Counter
    db = get_database()
    uid = current_user["id"]

    fav_docs = await db.favorites.find({"user_id": uid}).to_list(100)
    fav_ids = [f["movie_id"] for f in fav_docs]

    history_docs = await db.watch_history.find({"user_id": uid}).to_list(100)
    history_ids = [h["movie_id"] for h in history_docs]

    rating_docs = await db.ratings.find({"user_id": uid}).to_list(100)

    all_movie_ids = list(set(fav_ids + history_ids + [r["movie_id"] for r in rating_docs]))
    avg_rating = sum(r["rating"] for r in rating_docs) / len(rating_docs) if rating_docs else 0

    genre_counter: Counter = Counter()
    actor_counter: Counter = Counter()
    director_counter: Counter = Counter()
    year_counter: Counter = Counter()

    if all_movie_ids:
        cursor = db.movies.find({"id": {"$in": all_movie_ids}})
        async for movie in cursor:
            weight = 3 if movie["id"] in fav_ids else 1
            for g in (movie.get("genres") or []):
                genre_counter[g] += weight
            for c in (movie.get("cast") or [])[:5]:
                if isinstance(c, dict) and c.get("name"):
                    actor_counter[c["name"]] += weight
            if movie.get("director"):
                director_counter[movie["director"]] += weight
            if movie.get("release_year"):
                decade = f"{(movie['release_year'] // 10) * 10}s"
                year_counter[decade] += 1

    top_genres = [
        {"genre": g, "count": c, "percentage": round(c / max(sum(genre_counter.values()), 1) * 100)}
        for g, c in genre_counter.most_common(8)
    ]
    top_actors = [{"name": a, "count": c} for a, c in actor_counter.most_common(5) if a]
    top_directors = [{"name": d, "count": c} for d, c in director_counter.most_common(5) if d]
    favorite_decade = year_counter.most_common(1)[0][0] if year_counter else "2010s"

    engine = get_engine()
    personality_data = {}
    if engine:
        personality_data = engine.explainer.analyze_taste(dict(genre_counter), len(all_movie_ids))

    return TasteAnalysis(
        favorite_genres=top_genres,
        favorite_actors=top_actors,
        favorite_directors=top_directors,
        average_rating=round(avg_rating, 2),
        favorite_decade=favorite_decade,
        total_watched=len(set(history_ids)),
        total_rated=len(rating_docs),
        personality=personality_data.get("personality", "Cinephile"),
        personality_description=personality_data.get("personality_description", ""),
        genre_distribution=top_genres,
    )

"""Search routes: full-text, autocomplete, suggestions, voice using MongoDB Atlas."""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from datetime import datetime, timezone

from app.core.database import get_database
from app.core.utils import serialize_doc
from app.schemas.movie import MovieListResponse, PaginatedMovies
from app.schemas.recommendation import SearchSuggestion

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/", response_model=PaginatedMovies)
async def search_movies(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    genre: Optional[str] = None,
    year: Optional[int] = None,
    min_rating: float = Query(0.0, ge=0, le=10),
    sort: str = Query("relevance", regex="^(relevance|popularity|vote_average|release_year)$"),
):
    db = get_database()

    # Regex or text query search
    query_cond = {
        "$or": [
            {"title": {"$regex": q, "$options": "i"}},
            {"overview": {"$regex": q, "$options": "i"}},
            {"director": {"$regex": q, "$options": "i"}},
            {"tagline": {"$regex": q, "$options": "i"}},
        ]
    }

    if genre:
        query_cond["genres"] = genre
    if year:
        query_cond["release_year"] = year
    if min_rating > 0:
        query_cond["vote_average"] = {"$gte": min_rating}

    sort_key = "popularity" if sort == "relevance" else sort

    total = await db.movies.count_documents(query_cond)
    cursor = (
        db.movies.find(query_cond)
        .sort(sort_key, -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )

    movies = [serialize_doc(m) async for m in cursor]

    # Log search in MongoDB
    try:
        await db.search_history.insert_one({
            "query": q,
            "result_count": total,
            "created_at": datetime.now(timezone.utc),
        })
    except Exception:
        pass

    return PaginatedMovies(
        items=[MovieListResponse.model_validate(m) for m in movies],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page if total > 0 else 1,
    )


@router.get("/suggestions", response_model=List[SearchSuggestion])
async def get_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(8, ge=1, le=20),
):
    db = get_database()
    results = []

    # Movie title matches
    cursor = (
        db.movies.find({"title": {"$regex": f"^{q}", "$options": "i"}})
        .sort("popularity", -1)
        .limit(5)
    )
    async for m in cursor:
        results.append(SearchSuggestion(
            query=m["title"],
            type="movie",
            movie_id=m["id"],
            poster_path=m.get("poster_path"),
        ))

    # Director matches
    if len(results) < limit:
        directors = await db.movies.distinct("director", {"director": {"$regex": f"^{q}", "$options": "i"}})
        for d in directors[:3]:
            if d:
                results.append(SearchSuggestion(query=d, type="director"))

    return results[:limit]


@router.get("/trending-searches")
async def trending_searches(limit: int = Query(10, ge=1, le=20)):
    db = get_database()
    pipeline = [
        {"$group": {"_id": "$query", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    results = await db.search_history.aggregate(pipeline).to_list(limit)
    return [{"query": r["_id"], "count": r["count"]} for r in results if r.get("_id")]

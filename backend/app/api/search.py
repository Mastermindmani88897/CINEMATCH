"""
CineMatch AI — Search API Router
Comprehensive full-text, industry-mapped, actor/director/keyword/year search with TMDB fallback.
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from datetime import datetime, timezone

from app.core.database import get_database
from app.core.utils import serialize_doc
from app.schemas.movie import MovieListResponse, PaginatedMovies
from app.schemas.recommendation import SearchSuggestion
from app.services import tmdb_service
from app.api.movies import map_tmdb_to_list_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])

INDUSTRY_SEARCH_MAP = {
    "tollywood": {"$or": [{"original_language": "te"}, {"keywords": {"$regex": "tollywood|telugu", "$options": "i"}}, {"overview": {"$regex": "telugu", "$options": "i"}}]},
    "bollywood": {"$or": [{"original_language": "hi"}, {"keywords": {"$regex": "bollywood|hindi", "$options": "i"}}, {"overview": {"$regex": "bollywood|hindi", "$options": "i"}}]},
    "kollywood": {"$or": [{"original_language": "ta"}, {"keywords": {"$regex": "kollywood|tamil", "$options": "i"}}, {"overview": {"$regex": "tamil", "$options": "i"}}]},
    "mollywood": {"$or": [{"original_language": "ml"}, {"keywords": {"$regex": "mollywood|malayalam", "$options": "i"}}, {"overview": {"$regex": "malayalam", "$options": "i"}}]},
    "sandalwood": {"$or": [{"original_language": "kn"}, {"keywords": {"$regex": "sandalwood|kannada", "$options": "i"}}, {"overview": {"$regex": "kannada", "$options": "i"}}]},
    "hollywood": {"$or": [{"original_language": "en"}, {"origin_country": "US"}]},
    "anime": {"$or": [{"genres": "Animation", "original_language": "ja"}, {"genres": "Animation"}, {"overview": {"$regex": "anime", "$options": "i"}}]},
    "marvel": {"$or": [{"keywords": {"$regex": "marvel", "$options": "i"}}, {"production_companies": {"$regex": "marvel", "$options": "i"}}, {"title": {"$regex": "marvel|avengers|spider-man|iron man|thor|captain america|x-men|deadpool|wolverine|guardians of the galaxy|black panther|doctor strange|ant-man", "$options": "i"}}, {"overview": {"$regex": "marvel", "$options": "i"}}]},
    "sci-fi": {"genres": {"$regex": "Science Fiction|Sci-Fi", "$options": "i"}},
    "scifi": {"genres": {"$regex": "Science Fiction|Sci-Fi", "$options": "i"}},
    "science fiction": {"genres": {"$regex": "Science Fiction|Sci-Fi", "$options": "i"}},
    "action": {"genres": {"$regex": "Action", "$options": "i"}},
    "comedy": {"genres": {"$regex": "Comedy", "$options": "i"}},
    "horror": {"genres": {"$regex": "Horror", "$options": "i"}},
    "telugu": {"original_language": "te"},
    "hindi": {"original_language": "hi"},
    "english": {"original_language": "en"},
}


@router.get("", response_model=PaginatedMovies)
@router.get("/", response_model=PaginatedMovies, include_in_schema=False)
async def search_movies(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    genre: Optional[str] = None,
    year: Optional[int] = None,
    language: Optional[str] = None,
    min_rating: float = Query(0.0, ge=0, le=10),
    sort: str = Query("popularity", pattern="^(relevance|popularity|vote_average|release_year|weighted_rating)$"),
):
    try:
        db = get_database()
        q_clean = q.strip().lower()

        # Check industry/keyword aliases first
        if q_clean in INDUSTRY_SEARCH_MAP:
            query_cond = INDUSTRY_SEARCH_MAP[q_clean]
        elif q_clean.isdigit() and len(q_clean) == 4:
            query_cond = {"release_year": int(q_clean)}
        else:
            query_cond = {
                "$or": [
                    {"title": {"$regex": q, "$options": "i"}},
                    {"original_title": {"$regex": q, "$options": "i"}},
                    {"overview": {"$regex": q, "$options": "i"}},
                    {"director": {"$regex": q, "$options": "i"}},
                    {"cast.name": {"$regex": q, "$options": "i"}},
                    {"genres": {"$regex": q, "$options": "i"}},
                    {"original_language": {"$regex": q, "$options": "i"}},
                    {"origin_country": {"$regex": q, "$options": "i"}},
                    {"tagline": {"$regex": q, "$options": "i"}},
                    {"keywords": {"$regex": q, "$options": "i"}},
                ]
            }

        # Apply secondary filters if passed
        if genre:
            query_cond["genres"] = genre
        if year:
            query_cond["release_year"] = year
        if language:
            query_cond["original_language"] = language
        if min_rating > 0:
            query_cond["vote_average"] = {"$gte": min_rating}

        sort_key = "popularity" if sort == "relevance" else sort

        total = await db.movies.count_documents(query_cond)
        if total > 0:
            cursor = (
                db.movies.find(query_cond)
                .sort(sort_key, -1)
                .skip((page - 1) * per_page)
                .limit(per_page)
            )

            movies = [serialize_doc(m) async for m in cursor]

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
                pages=(total + per_page - 1) // per_page,
            )
    except Exception as e:
        logger.warning(f"MongoDB search query failed ({e}). Falling back to TMDB Search API...")

    # Fallback to TMDB Search API
    try:
        tmdb_data = await tmdb_service.search_tmdb_movies(query=q, page=page)
        results = tmdb_data.get("results", [])
        items = [MovieListResponse.model_validate(map_tmdb_to_list_response(item)) for item in results[:per_page]]
        total_results = tmdb_data.get("total_results", len(items))

        return PaginatedMovies(
            items=items,
            total=total_results,
            page=page,
            per_page=per_page,
            pages=tmdb_data.get("total_pages", 1),
        )
    except Exception as exc:
        logger.warning(f"TMDB search fallback notice: {exc}")
        return PaginatedMovies(
            items=[],
            total=0,
            page=page,
            per_page=per_page,
            pages=0,
        )


@router.get("/suggestions", response_model=List[SearchSuggestion])
async def get_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(8, ge=1, le=20),
):
    results = []
    try:
        db = get_database()
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

        if len(results) < limit:
            directors = await db.movies.distinct("director", {"director": {"$regex": f"^{q}", "$options": "i"}})
            for d in directors[:3]:
                if d:
                    results.append(SearchSuggestion(query=d, type="director"))
        if results:
            return results[:limit]
    except Exception as e:
        logger.warning(f"MongoDB suggestions query failed ({e}). Falling back to TMDB Search API...")

    # Fallback to TMDB search suggestions
    try:
        tmdb_data = await tmdb_service.search_tmdb_movies(query=q, page=1)
        for m in tmdb_data.get("results", [])[:limit]:
            results.append(SearchSuggestion(
                query=m.get("title", ""),
                type="movie",
                movie_id=m.get("id", 1),
                poster_path=m.get("poster_path"),
            ))
    except Exception as exc:
        logger.warning(f"TMDB suggestions fallback notice: {exc}")

    return results[:limit]


@router.get("/trending-searches")
async def trending_searches(limit: int = Query(10, ge=1, le=20)):
    try:
        db = get_database()
        pipeline = [
            {"$group": {"_id": "$query", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
        results = await db.search_history.aggregate(pipeline).to_list(limit)
        if results:
            return [{"query": r["_id"], "count": r["count"]} for r in results if r.get("_id")]
    except Exception:
        pass

    # Default trending suggestions
    return [
        {"query": "Tollywood", "count": 140},
        {"query": "Bollywood", "count": 130},
        {"query": "Inception", "count": 120},
        {"query": "Marvel", "count": 110},
        {"query": "Anime", "count": 95},
    ][:limit]

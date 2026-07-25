"""
Movie routes: list, detail, trending, popular, top-rated, upcoming, genres using MongoDB Atlas with live TMDB API fallbacks.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from app.core.database import get_database
from app.core.utils import serialize_doc
from app.schemas.movie import MovieResponse, MovieListResponse, PaginatedMovies
from app.services import tmdb_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/movies", tags=["Movies"])

TMDB_GENRES_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}


def map_tmdb_to_list_response(item: dict) -> dict:
    tmdb_id = item.get("id") or 1
    title = item.get("title") or item.get("name") or "Untitled"
    release_date = item.get("release_date") or item.get("first_air_date") or ""
    release_year = int(release_date[:4]) if len(release_date) >= 4 and release_date[:4].isdigit() else 2024

    genres = []
    if "genres" in item and isinstance(item["genres"], list):
        genres = [g.get("name") if isinstance(g, dict) else str(g) for g in item["genres"]]
    elif "genre_ids" in item and isinstance(item["genre_ids"], list):
        genres = [TMDB_GENRES_MAP.get(gid, "Drama") for gid in item["genre_ids"]]

    vote_avg = float(item.get("vote_average") or 0.0)

    return {
        "id": int(tmdb_id),
        "tmdb_id": int(tmdb_id),
        "title": str(title),
        "overview": str(item.get("overview") or ""),
        "genres": genres,
        "release_year": release_year,
        "vote_average": vote_avg,
        "popularity": float(item.get("popularity") or 0.0),
        "weighted_rating": round(vote_avg, 2),
        "poster_path": item.get("poster_path"),
        "backdrop_path": item.get("backdrop_path"),
        "runtime": int(item.get("runtime") or 120),
        "original_language": str(item.get("original_language") or "en"),
    }


def map_tmdb_to_detail_response(item: dict) -> dict:
    base = map_tmdb_to_list_response(item)
    base.update({
        "tagline": str(item.get("tagline") or ""),
        "keywords": [k.get("name") for k in item.get("keywords", {}).get("keywords", [])] if isinstance(item.get("keywords"), dict) else [],
        "cast": [],
        "crew": [],
        "director": "",
        "production_companies": [p.get("name") for p in item.get("production_companies", [])] if isinstance(item.get("production_companies"), list) else [],
        "trailer_key": None,
        "imdb_id": item.get("imdb_id"),
        "budget": float(item.get("budget") or 0),
        "revenue": float(item.get("revenue") or 0),
        "trending_score": float(item.get("popularity") or 0.0),
        "created_at": datetime.now(),
    })
    return base


@router.get("", response_model=PaginatedMovies)
@router.get("/", response_model=PaginatedMovies)
@router.get("/discover", response_model=PaginatedMovies)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    genre: Optional[str] = None,
    year: Optional[int] = None,
    language: Optional[str] = None,
    country: Optional[str] = None,
    min_rating: float = Query(0, ge=0, le=10),
    sort: str = Query("popularity", pattern="^(popularity|vote_average|release_year|weighted_rating)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    try:
        db = get_database()
        query = {}
        if genre:
            query["genres"] = genre
        if year:
            query["release_year"] = year
        if language:
            query["original_language"] = language
        if country:
            query["origin_country"] = country
        if min_rating > 0:
            query["vote_average"] = {"$gte": min_rating}

        sort_order = -1 if order == "desc" else 1

        total = await db.movies.count_documents(query)
        if total > 0:
            cursor = (
                db.movies.find(query)
                .sort(sort, sort_order)
                .skip((page - 1) * per_page)
                .limit(per_page)
            )
            movies = [serialize_doc(m) async for m in cursor]
            return PaginatedMovies(
                items=[MovieListResponse.model_validate(m) for m in movies],
                total=total,
                page=page,
                per_page=per_page,
                pages=(total + per_page - 1) // per_page,
            )
    except Exception as e:
        logger.warning(f"MongoDB query failed in list_movies ({e}). Falling back to TMDB API...")

    # TMDB Fallback
    try:
        tmdb_data = await tmdb_service.get_popular_movies(page=page)
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
        logger.warning(f"TMDB fallback failed in list_movies: {exc}")
        return PaginatedMovies(
            items=[],
            total=0,
            page=page,
            per_page=per_page,
            pages=0,
        )


@router.get("/trending", response_model=List[MovieListResponse])
async def get_trending(limit: int = Query(20, le=50)):
    try:
        db = get_database()
        cursor = db.movies.find({}).sort("trending_score", -1).limit(limit)
        movies = [serialize_doc(m) async for m in cursor]
        if movies:
            return [MovieListResponse.model_validate(m) for m in movies]
    except Exception as e:
        logger.warning(f"MongoDB query failed in get_trending ({e}). Falling back to TMDB API...")

    tmdb_data = await tmdb_service.get_trending_movies(time_window="day", page=1)
    results = tmdb_data.get("results", [])
    return [MovieListResponse.model_validate(map_tmdb_to_list_response(m)) for m in results[:limit]]


@router.get("/popular", response_model=List[MovieListResponse])
async def get_popular(limit: int = Query(20, le=50)):
    try:
        db = get_database()
        cursor = db.movies.find({}).sort("popularity", -1).limit(limit)
        movies = [serialize_doc(m) async for m in cursor]
        if movies:
            return [MovieListResponse.model_validate(m) for m in movies]
    except Exception as e:
        logger.warning(f"MongoDB query failed in get_popular ({e}). Falling back to TMDB API...")

    tmdb_data = await tmdb_service.get_popular_movies(page=1)
    results = tmdb_data.get("results", [])
    return [MovieListResponse.model_validate(map_tmdb_to_list_response(m)) for m in results[:limit]]


@router.get("/top-rated", response_model=List[MovieListResponse])
async def get_top_rated(
    limit: int = Query(20, le=50),
    min_votes: int = Query(100, ge=0),
):
    try:
        db = get_database()
        cursor = (
            db.movies.find({"vote_count": {"$gte": min_votes}})
            .sort("weighted_rating", -1)
            .limit(limit)
        )
        movies = [serialize_doc(m) async for m in cursor]
        if movies:
            return [MovieListResponse.model_validate(m) for m in movies]
    except Exception as e:
        logger.warning(f"MongoDB query failed in get_top_rated ({e}). Falling back to TMDB API...")

    tmdb_data = await tmdb_service.get_top_rated_movies(page=1)
    results = tmdb_data.get("results", [])
    return [MovieListResponse.model_validate(map_tmdb_to_list_response(m)) for m in results[:limit]]


@router.get("/upcoming", response_model=List[MovieListResponse])
async def get_upcoming(limit: int = Query(20, le=50)):
    try:
        db = get_database()
        current_year = datetime.now().year
        cursor = (
            db.movies.find({"release_year": {"$gte": current_year - 1}})
            .sort("popularity", -1)
            .limit(limit)
        )
        movies = [serialize_doc(m) async for m in cursor]
        if movies:
            return [MovieListResponse.model_validate(m) for m in movies]
    except Exception as e:
        logger.warning(f"MongoDB query failed in get_upcoming ({e}). Falling back to TMDB API...")

    tmdb_data = await tmdb_service.get_upcoming_movies(page=1)
    results = tmdb_data.get("results", [])
    return [MovieListResponse.model_validate(map_tmdb_to_list_response(m)) for m in results[:limit]]


@router.get("/genres")
async def get_genres():
    try:
        db = get_database()
        genres = await db.movies.distinct("genres")
        if genres:
            return sorted([g for g in genres if g])
    except Exception as e:
        logger.warning(f"MongoDB query failed in get_genres ({e}). Returning default genres...")

    return sorted(list(set(TMDB_GENRES_MAP.values())))


@router.get("/discover", response_model=PaginatedMovies)
async def discover_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    genre: Optional[str] = None,
    year: Optional[int] = None,
    language: Optional[str] = None,
    country: Optional[str] = None,
    min_rating: float = Query(0, ge=0, le=10),
    sort: str = Query("popularity", pattern="^(popularity|vote_average|release_year|weighted_rating)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    return await list_movies(
        page=page,
        per_page=per_page,
        genre=genre,
        year=year,
        language=language,
        country=country,
        min_rating=min_rating,
        sort=sort,
        order=order,
    )


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int):
    try:
        db = get_database()
        # 1. Primary lookup by internal ID
        movie = await db.movies.find_one({"id": movie_id})
        # 2. Secondary lookup by TMDB ID if internal ID not found
        if not movie:
            movie = await db.movies.find_one({"tmdb_id": movie_id})
        if movie:
            return MovieResponse.model_validate(serialize_doc(movie))
    except Exception as e:
        logger.warning(f"MongoDB query failed in get_movie ({e}). Falling back to TMDB API...")

    # Fetch from TMDB API
    try:
        tmdb_item = await tmdb_service.get_movie_details(movie_id)
        if tmdb_item:
            return MovieResponse.model_validate(map_tmdb_to_detail_response(tmdb_item))
    except Exception:
        pass

    raise HTTPException(status_code=404, detail="Movie not found")

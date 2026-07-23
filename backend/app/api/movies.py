"""Movie routes: list, detail, trending, popular, top-rated, upcoming, genres using MongoDB Atlas."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from app.core.database import get_database
from app.core.utils import serialize_doc
from app.schemas.movie import MovieResponse, MovieListResponse, PaginatedMovies

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=PaginatedMovies)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    genre: Optional[str] = None,
    year: Optional[int] = None,
    min_rating: float = Query(0, ge=0, le=10),
    sort: str = Query("popularity", regex="^(popularity|vote_average|release_year|weighted_rating)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
):
    db = get_database()
    query = {}

    if genre:
        query["genres"] = genre
    if year:
        query["release_year"] = year
    if min_rating > 0:
        query["vote_average"] = {"$gte": min_rating}

    sort_order = -1 if order == "desc" else 1

    total = await db.movies.count_documents(query)
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
        pages=(total + per_page - 1) // per_page if total > 0 else 1,
    )


@router.get("/trending", response_model=List[MovieListResponse])
async def get_trending(limit: int = Query(20, le=50)):
    db = get_database()
    cursor = db.movies.find({}).sort("trending_score", -1).limit(limit)
    movies = [serialize_doc(m) async for m in cursor]
    return [MovieListResponse.model_validate(m) for m in movies]


@router.get("/popular", response_model=List[MovieListResponse])
async def get_popular(limit: int = Query(20, le=50)):
    db = get_database()
    cursor = db.movies.find({}).sort("popularity", -1).limit(limit)
    movies = [serialize_doc(m) async for m in cursor]
    return [MovieListResponse.model_validate(m) for m in movies]


@router.get("/top-rated", response_model=List[MovieListResponse])
async def get_top_rated(
    limit: int = Query(20, le=50),
    min_votes: int = Query(100, ge=0),
):
    db = get_database()
    cursor = (
        db.movies.find({"vote_count": {"$gte": min_votes}})
        .sort("weighted_rating", -1)
        .limit(limit)
    )
    movies = [serialize_doc(m) async for m in cursor]
    return [MovieListResponse.model_validate(m) for m in movies]


@router.get("/upcoming", response_model=List[MovieListResponse])
async def get_upcoming(limit: int = Query(20, le=50)):
    db = get_database()
    current_year = datetime.now().year
    cursor = (
        db.movies.find({"release_year": {"$gte": current_year - 1}})
        .sort("popularity", -1)
        .limit(limit)
    )
    movies = [serialize_doc(m) async for m in cursor]
    return [MovieListResponse.model_validate(m) for m in movies]


@router.get("/genres")
async def get_genres():
    db = get_database()
    genres = await db.movies.distinct("genres")
    return sorted([g for g in genres if g])


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int):
    db = get_database()
    movie = await db.movies.find_one({"$or": [{"id": movie_id}, {"tmdb_id": movie_id}]})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return MovieResponse.model_validate(serialize_doc(movie))

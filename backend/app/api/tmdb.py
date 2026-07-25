"""
CineMatch AI — TMDB Direct API Router
Provides endpoints for TMDB trending, popular, upcoming, top-rated, search, details, cast, trailers, and poster helper.
"""

from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional, Dict, Any
from app.services import tmdb_service

router = APIRouter(prefix="/tmdb", tags=["TMDB Integration"])


@router.get("/trending")
async def get_trending(
    time_window: str = Query("day", pattern="^(day|week)$"),
    page: int = Query(1, ge=1)
) -> Dict[str, Any]:
    """Get trending movies from TMDB API."""
    return await tmdb_service.get_trending_movies(time_window=time_window, page=page)


@router.get("/popular")
async def get_popular(page: int = Query(1, ge=1)) -> Dict[str, Any]:
    """Get popular movies from TMDB API."""
    return await tmdb_service.get_popular_movies(page=page)


@router.get("/upcoming")
async def get_upcoming(page: int = Query(1, ge=1)) -> Dict[str, Any]:
    """Get upcoming movies from TMDB API."""
    return await tmdb_service.get_upcoming_movies(page=page)


@router.get("/top-rated")
async def get_top_rated(page: int = Query(1, ge=1)) -> Dict[str, Any]:
    """Get top rated movies from TMDB API."""
    return await tmdb_service.get_top_rated_movies(page=page)


@router.get("/search")
async def search_movies(
    q: str = Query(..., min_length=1, description="Movie title search query"),
    page: int = Query(1, ge=1)
) -> Dict[str, Any]:
    """Search for movies on TMDB."""
    return await tmdb_service.search_tmdb_movies(query=q, page=page)


@router.get("/movie/{movie_id}")
async def get_movie_details(movie_id: int) -> Dict[str, Any]:
    """Get detailed information for a movie from TMDB."""
    return await tmdb_service.get_movie_details(movie_id=movie_id)


@router.get("/movie/{movie_id}/cast")
async def get_movie_cast(movie_id: int) -> Dict[str, Any]:
    """Get cast and crew for a movie from TMDB."""
    return await tmdb_service.get_movie_cast(movie_id=movie_id)


@router.get("/movie/{movie_id}/trailers")
async def get_movie_trailers(movie_id: int) -> Dict[str, Any]:
    """Get videos and trailers for a movie from TMDB."""
    return await tmdb_service.get_movie_trailers(movie_id=movie_id)


@router.get("/poster")
async def get_poster_url(
    path: str = Query(..., description="TMDB poster image path e.g. /q6y0Go1tsGEsmtFryDO23R9y0eX.jpg"),
    size: str = Query("w500", pattern="^(w92|w154|w185|w342|w500|w780|original)$")
) -> Dict[str, Any]:
    """Construct full TMDB poster image URL."""
    url = tmdb_service.get_poster_url(poster_path=path, size=size)
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid poster path")
    return {"url": url}

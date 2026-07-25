"""
CineMatch AI — TMDB Integration Service
Provides wrapper methods for TMDB API v3 endpoints using TMDB_API_KEY from environment variables.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
import httpx
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_api_key() -> str:
    api_key = settings.TMDB_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TMDB_API_KEY is missing from environment variables."
        )
    return api_key


TMDB_EDGE_IPS = ["13.224.238.99", "13.224.238.29", "13.224.238.48"]


async def _tmdb_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    api_key = _get_api_key()
    query_params = {"api_key": api_key}
    if params:
        query_params.update(params)

    clean_ep = endpoint.lstrip("/")
    headers = {
        "Host": "api.themoviedb.org",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    last_error = None

    # 1. Primary Strategy: Try direct edge IPs for fast connection
    for ip in TMDB_EDGE_IPS:
        edge_url = f"https://{ip}/3/{clean_ep}"
        try:
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                resp = await client.get(edge_url, params=query_params, headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code in (401, 403):
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TMDB API key.")
                elif resp.status_code == 404:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource not found: {endpoint}")
        except HTTPException:
            raise
        except Exception as ex:
            last_error = ex
            continue

    # 2. Secondary Strategy: Standard Hostname with Retries & Exponential Backoff (30s timeout)
    url = f"{settings.TMDB_BASE_URL.rstrip('/')}/{clean_ep}"
    backoff_delays = [1.0, 2.0, 4.0]

    for delay in backoff_delays:
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(url, params=query_params, headers={"User-Agent": headers["User-Agent"]})
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code in (401, 403):
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TMDB API key.")
                elif resp.status_code == 404:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource not found: {endpoint}")
                elif resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail=f"TMDB API returned error: {resp.text}")
        except HTTPException:
            raise
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(delay)

    err_msg = str(last_error) if last_error else "ConnectTimeout after retries"
    logger.error(f"TMDB Network Error: {err_msg}")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Failed to connect to TMDB API: {err_msg}"
    )


async def get_trending_movies(time_window: str = "day", page: int = 1) -> Dict[str, Any]:
    """Fetch trending movies from TMDB."""
    return await _tmdb_request(f"trending/movie/{time_window}", {"page": page})


async def get_popular_movies(page: int = 1) -> Dict[str, Any]:
    """Fetch popular movies from TMDB."""
    return await _tmdb_request("movie/popular", {"page": page})


async def get_upcoming_movies(page: int = 1) -> Dict[str, Any]:
    """Fetch upcoming movies from TMDB."""
    return await _tmdb_request("movie/upcoming", {"page": page})


async def get_top_rated_movies(page: int = 1) -> Dict[str, Any]:
    """Fetch top rated movies from TMDB."""
    return await _tmdb_request("movie/top_rated", {"page": page})


async def search_tmdb_movies(query: str, page: int = 1) -> Dict[str, Any]:
    """Search for movies on TMDB by query."""
    if not query.strip():
        return {"results": [], "page": 1, "total_results": 0, "total_pages": 0}
    return await _tmdb_request("search/movie", {"query": query, "page": page})


async def get_movie_details(movie_id: int) -> Dict[str, Any]:
    """Fetch movie details from TMDB."""
    return await _tmdb_request(f"movie/{movie_id}")


async def get_movie_cast(movie_id: int) -> Dict[str, Any]:
    """Fetch credits/cast for a movie from TMDB."""
    return await _tmdb_request(f"movie/{movie_id}/credits")


async def get_movie_trailers(movie_id: int) -> Dict[str, Any]:
    """Fetch videos/trailers for a movie from TMDB."""
    return await _tmdb_request(f"movie/{movie_id}/videos")


async def get_now_playing_movies(page: int = 1) -> Dict[str, Any]:
    """Fetch currently playing movies in theaters from TMDB."""
    return await _tmdb_request("movie/now_playing", {"page": page})


async def discover_movies(
    language: Optional[str] = None,
    region: Optional[str] = None,
    sort_by: str = "popularity.desc",
    page: int = 1,
    with_genres: Optional[str] = None,
) -> Dict[str, Any]:
    """Discover movies by language, region, genre, and popularity on TMDB."""
    params: Dict[str, Any] = {"page": page, "sort_by": sort_by}
    if language:
        params["with_original_language"] = language
    if region:
        params["region"] = region
    if with_genres:
        params["with_genres"] = with_genres
    return await _tmdb_request("discover/movie", params)


async def get_movie_watch_providers(movie_id: int) -> Dict[str, Any]:
    """Fetch streaming watch providers for a movie from TMDB."""
    return await _tmdb_request(f"movie/{movie_id}/watch/providers")


def get_poster_url(poster_path: Optional[str], size: str = "w500") -> Optional[str]:
    """Construct full TMDB poster image URL."""
    if not poster_path:
        return None
    base = settings.TMDB_IMAGE_BASE_URL.rstrip('/')
    return f"{base}/{size}/{poster_path.lstrip('/')}"

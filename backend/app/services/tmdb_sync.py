"""
CineMatch AI — TMDB Live Synchronization & ML Hot-Reload Service
Fetches real movie data from TMDB API across multi-regional industries (Hollywood, Bollywood, Tollywood, Kollywood, Mollywood, Sandalwood, Korean, Anime, Spanish, French),
inserts/updates into MongoDB, deduplicates by tmdb_id, retrains the ML model, and hot-reloads it in real-time.
"""

import logging
import asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.database import get_database

logger = logging.getLogger(__name__)

TMDB_GENRES_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}

# Industry language map (Hollywood, Bollywood, Tollywood, Kollywood, Mollywood, Sandalwood, Korean, Japanese, Chinese, French, Spanish, Italian, German, Turkish)
LANGUAGES = ["en", "hi", "te", "ta", "ml", "kn", "ko", "ja", "zh", "fr", "es", "it", "de", "tr"]


async def _upsert_movie_item(item: dict, db) -> bool:
    tmdb_id = item.get("id")
    title = item.get("title") or item.get("original_title") or item.get("name")
    if not tmdb_id or not title:
        return False

    existing = await db.movies.find_one({"tmdb_id": tmdb_id})

    release_date = item.get("release_date") or item.get("first_air_date") or ""
    release_year = int(release_date[:4]) if len(release_date) >= 4 and release_date[:4].isdigit() else 2024

    genres = []
    if "genres" in item and isinstance(item["genres"], list):
        genres = [g.get("name") if isinstance(g, dict) else str(g) for g in item["genres"]]
    elif "genre_ids" in item and isinstance(item["genre_ids"], list):
        genres = [TMDB_GENRES_MAP.get(gid, "Drama") for gid in item["genre_ids"]]

    vote_avg = float(item.get("vote_average") or 0.0)
    vote_cnt = int(item.get("vote_count") or 0)
    pop = float(item.get("popularity") or 0.0)

    # Calculate weighted rating: (v/(v+m) * R) + (m/(v+m) * C)
    m = 100
    c_rating = 7.0
    weighted_rating = round((vote_cnt / (vote_cnt + m) * vote_avg) + (m / (vote_cnt + m) * c_rating), 2)

    cast = item.get("cast", [])
    director = item.get("director", "")
    crew = item.get("crew", [])
    production_companies = item.get("production_companies", [])
    if isinstance(production_companies, list):
        production_companies = [p.get("name") if isinstance(p, dict) else str(p) for p in production_companies]

    doc = {
        "tmdb_id": int(tmdb_id),
        "title": str(title),
        "original_title": str(item.get("original_title") or title),
        "overview": str(item.get("overview") or ""),
        "genres": genres,
        "release_date": str(release_date),
        "release_year": release_year,
        "vote_average": vote_avg,
        "vote_count": vote_cnt,
        "popularity": pop,
        "weighted_rating": weighted_rating,
        "trending_score": round(pop * 0.7 + vote_avg * 0.3, 2),
        "poster_path": item.get("poster_path"),
        "backdrop_path": item.get("backdrop_path"),
        "original_language": str(item.get("original_language") or "en"),
        "origin_country": item.get("origin_country") or (item.get("production_countries", [{}])[0].get("iso_3166_1") if item.get("production_countries") else "US"),
        "runtime": int(item.get("runtime") or 120),
        "tagline": str(item.get("tagline") or ""),
        "cast": cast,
        "director": director,
        "crew": crew,
        "production_companies": production_companies,
        "trailer_key": item.get("trailer_key"),
        "watch_providers": item.get("watch_providers", []),
        "updated_at": datetime.now(timezone.utc),
    }

    if existing:
        await db.movies.update_one({"_id": existing["_id"]}, {"$set": doc})
        return False
    else:
        count = await db.movies.count_documents({})
        doc["id"] = count + 1
        doc["created_at"] = datetime.now(timezone.utc)
        await db.movies.insert_one(doc)
        return True


TMDB_EDGE_IPS = ["13.224.238.99", "13.224.238.29", "13.224.238.48"]


async def _fetch_tmdb_json(url_path: str, params: dict) -> tuple[Optional[dict], bool]:
    """Resilient TMDB fetcher with Edge IP fallback, 30s timeout, and exponential backoff retries."""
    headers = {
        "Host": "api.themoviedb.org",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    # 1. Try edge IPs first
    for ip in TMDB_EDGE_IPS:
        edge_url = f"https://{ip}/3/{url_path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                resp = await client.get(edge_url, params=params, headers=headers)
                if resp.status_code == 200:
                    return resp.json(), True
        except Exception:
            continue

    # 2. Try standard URL with backoff retries
    standard_url = f"{settings.TMDB_BASE_URL.rstrip('/')}/{url_path.lstrip('/')}"
    for delay in [1.0, 2.0]:
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(standard_url, params=params, headers={"User-Agent": headers["User-Agent"]})
                if resp.status_code == 200:
                    return resp.json(), True
        except Exception:
            await asyncio.sleep(delay)

    return None, False


async def sync_tmdb_movies(max_pages_per_lang: int = 5) -> dict:
    """Multi-industry, multi-page batch sync from TMDB API targeting 1000+ movies."""
    if not settings.TMDB_API_KEY:
        logger.info("TMDB_API_KEY not configured — skipping live API fetch")
        return {"status": "unconfigured", "synced": 0}

    logger.info("Starting multi-industry TMDB movie synchronization...")
    db = get_database()
    if db is None:
        return {"status": "no_db", "synced": 0}

    synced_count = 0
    updated_count = 0
    total_requests = 0
    total_pages = 0

    # 1. Standard Popular, Top Rated, Upcoming, Now Playing categories
    for category in ["popular", "top_rated", "upcoming", "now_playing"]:
        for page in range(1, max_pages_per_lang + 1):
            total_requests += 1
            data, ok = await _fetch_tmdb_json(f"movie/{category}", {"api_key": settings.TMDB_API_KEY, "page": page})
            if ok and data:
                total_pages += 1
                for item in data.get("results", []):
                    is_new = await _upsert_movie_item(item, db)
                    if is_new:
                        synced_count += 1
                    else:
                        updated_count += 1

    # 2. Multi-language / Industry Discover endpoints
    for lang in LANGUAGES:
        for page in range(1, max_pages_per_lang + 1):
            total_requests += 1
            params = {
                "api_key": settings.TMDB_API_KEY,
                "with_original_language": lang,
                "sort_by": "popularity.desc",
                "page": page,
            }
            data, ok = await _fetch_tmdb_json("discover/movie", params)
            if ok and data:
                total_pages += 1
                for item in data.get("results", []):
                    is_new = await _upsert_movie_item(item, db)
                    if is_new:
                        synced_count += 1
                    else:
                        updated_count += 1

    total_in_db = await db.movies.count_documents({})
    logger.info(f"TMDB Sync Complete ✓ New: {synced_count}, Updated: {updated_count}, Requests: {total_requests}, Pages: {total_pages}, Total in DB: {total_in_db}")

    # Retrain ML recommendation models automatically
    try:
        import sys, os
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        from ml.train import train_pipeline
        train_pipeline(skip_semantic=True)
        logger.info("ML recommendation models retrained successfully ✓")
    except Exception as ml_err:
        logger.warning(f"ML auto-retrain warning: {ml_err}")

    return {
        "status": "success",
        "new_movies": synced_count,
        "updated_movies": updated_count,
        "total_movies": total_in_db,
    }


async def schedule_daily_sync():
    """Background loop that runs periodic sync every 24 hours."""
    while True:
        try:
            await sync_tmdb_movies(max_pages_per_lang=2)
        except Exception as e:
            logger.error(f"Scheduled sync error: {e}")
        await asyncio.sleep(86400)


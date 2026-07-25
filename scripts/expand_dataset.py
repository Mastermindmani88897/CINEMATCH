"""
CineMatch AI — Massive Dataset Expansion Script (20,000+ Movies)
Fetches thousands of movies from TMDB API across multi-regional industries, decades, genres, and categories,
upserting them into MongoDB Atlas with complete metadata.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
import httpx
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

# Set up path to include root directory
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dataset_expander")

TMDB_GENRES_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}

LANGUAGES = ["te", "hi", "ta", "ml", "kn", "en", "ko", "ja", "zh", "fr", "es", "de", "it", "tr", "pt", "ru"]

DECADES = [
    ("1970-01-01", "1979-12-31"),
    ("1980-01-01", "1989-12-31"),
    ("1990-01-01", "1999-12-31"),
    ("2000-01-01", "2009-12-31"),
    ("2010-01-01", "2019-12-31"),
    ("2020-01-01", "2026-12-31"),
]

GENRE_IDS = list(TMDB_GENRES_MAP.keys())

TMDB_EDGE_IPS = ["13.224.238.99", "13.224.238.29", "13.224.238.48"]


async def fetch_tmdb_page(client: httpx.AsyncClient, endpoint: str, params: dict) -> list:
    """Fetch single TMDB page with resilient fallback and retries."""
    params["api_key"] = settings.TMDB_API_KEY
    headers = {
        "Host": "api.themoviedb.org",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    # Edge IP attempt
    for ip in TMDB_EDGE_IPS:
        edge_url = f"https://{ip}/3/{endpoint.lstrip('/')}"
        try:
            resp = await client.get(edge_url, params=params, headers=headers, timeout=15.0)
            if resp.status_code == 200:
                return resp.json().get("results", [])
        except Exception:
            continue

    # Standard URL fallback
    url = f"{settings.TMDB_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    for delay in [0.5, 1.0]:
        try:
            resp = await client.get(url, params={"api_key": settings.TMDB_API_KEY, **params}, timeout=15.0)
            if resp.status_code == 200:
                return resp.json().get("results", [])
        except Exception:
            await asyncio.sleep(delay)

    return []


def transform_tmdb_item(item: dict, next_id: int) -> dict:
    tmdb_id = item.get("id")
    title = item.get("title") or item.get("original_title") or item.get("name") or "Untitled"
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

    m = 100
    c_rating = 7.0
    weighted_rating = round((vote_cnt / (vote_cnt + m) * vote_avg) + (m / (vote_cnt + m) * c_rating), 2)

    return {
        "id": next_id,
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
        "cast": item.get("cast", []),
        "director": item.get("director", ""),
        "keywords": item.get("keywords", []),
        "updated_at": datetime.now(timezone.utc),
    }


async def main():
    logger.info("Starting Massive TMDB Dataset Expansion Target: 20,000+ Movies...")

    mongo_uri = settings.MONGODB_URI or "mongodb://localhost:27017"
    client_db = AsyncIOMotorClient(mongo_uri)
    db = client_db[settings.DATABASE_NAME]

    current_count = await db.movies.count_documents({})
    logger.info(f"Initial MongoDB Movie Count: {current_count}")

    existing_tmdb_ids = set()
    cursor = db.movies.find({}, {"tmdb_id": 1, "id": 1})
    max_internal_id = current_count
    async for doc in cursor:
        if "tmdb_id" in doc:
            existing_tmdb_ids.add(doc["tmdb_id"])
        if "id" in doc and doc["id"] > max_internal_id:
            max_internal_id = doc["id"]

    next_id = max_internal_id + 1
    new_movies_buffer = []

    async with httpx.AsyncClient(verify=False) as http_client:
        tasks = []

        # 1. Multi-language discovery (50 pages each language)
        for lang in LANGUAGES:
            for page in range(1, 51):
                tasks.append(fetch_tmdb_page(http_client, "discover/movie", {
                    "with_original_language": lang,
                    "sort_by": "popularity.desc",
                    "page": page,
                    "vote_count.gte": 5,
                }))

        # 2. Multi-decade & Genre discovery
        for g_id in GENRE_IDS:
            for g_date_start, g_date_end in DECADES:
                for page in range(1, 11):
                    tasks.append(fetch_tmdb_page(http_client, "discover/movie", {
                        "with_genres": g_id,
                        "primary_release_date.gte": g_date_start,
                        "primary_release_date.lte": g_date_end,
                        "sort_by": "popularity.desc",
                        "page": page,
                    }))

        # 3. Standard Popular, Top Rated, Trending
        for category in ["popular", "top_rated", "upcoming", "now_playing"]:
            for page in range(1, 51):
                tasks.append(fetch_tmdb_page(http_client, f"movie/{category}", {"page": page}))

        logger.info(f"Queued {len(tasks)} TMDB discovery tasks. Executing in batches...")

        batch_size = 20
        total_fetched = 0
        total_upserted = 0

        for i in range(0, len(tasks), batch_size):
            chunk = tasks[i:i + batch_size]
            results = await asyncio.gather(*chunk, return_exceptions=True)

            ops = []
            for res in results:
                if isinstance(res, list):
                    for item in res:
                        tmdb_id = item.get("id")
                        if not tmdb_id:
                            continue
                        total_fetched += 1
                        if tmdb_id not in existing_tmdb_ids:
                            existing_tmdb_ids.add(tmdb_id)
                            doc = transform_tmdb_item(item, next_id)
                            next_id += 1
                            ops.append(UpdateOne({"tmdb_id": tmdb_id}, {"$setOnInsert": doc}, upsert=True))
                        else:
                            # Update ratings and popularity
                            pop = float(item.get("popularity") or 0.0)
                            vote_avg = float(item.get("vote_average") or 0.0)
                            vote_cnt = int(item.get("vote_count") or 0)
                            ops.append(UpdateOne(
                                {"tmdb_id": tmdb_id},
                                {"$set": {
                                    "popularity": pop,
                                    "vote_average": vote_avg,
                                    "vote_count": vote_cnt,
                                    "trending_score": round(pop * 0.7 + vote_avg * 0.3, 2),
                                }}
                            ))

            if ops:
                res_bulk = await db.movies.bulk_write(ops, ordered=False)
                total_upserted += (res_bulk.upserted_count + res_bulk.modified_count)

            if i % 100 == 0:
                current_total = await db.movies.count_documents({})
                logger.info(f"Progress: Processed batch {i}/{len(tasks)} | Current DB Total: {current_total} movies")

            await asyncio.sleep(0.1)

    final_count = await db.movies.count_documents({})
    logger.info(f"🎉 Dataset Expansion Complete! Final MongoDB Total: {final_count} movies (Added/Updated: {total_upserted})")
    client_db.close()


if __name__ == "__main__":
    asyncio.run(main())

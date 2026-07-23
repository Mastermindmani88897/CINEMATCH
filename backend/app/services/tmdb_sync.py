"""
CineMatch AI — TMDB Live Synchronization & ML Hot-Reload Service
Fetches new movie data from TMDB API, inserts into MongoDB Atlas,
removes duplicates, retrains the ML model, and hot-reloads it in real-time.
"""

import logging
import asyncio
import httpx
from datetime import datetime, timezone
from app.core.config import settings
from app.core.database import get_database

logger = logging.getLogger(__name__)


async def sync_tmdb_movies():
    """Fetch popular/trending movies from TMDB API and upsert into MongoDB."""
    if not settings.TMDB_API_KEY:
        logger.info("TMDB_API_KEY not set — skipping live API fetch")
        return

    logger.info("Starting TMDB movie synchronization...")
    db = get_database()
    url = f"{settings.TMDB_BASE_URL}/movie/popular?api_key={settings.TMDB_API_KEY}&page=1"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"TMDB API request failed with status {resp.status_code}")
                return
            data = resp.json()
            results = data.get("results", [])

            synced_count = 0
            for item in results:
                tmdb_id = item.get("id")
                title = item.get("title")
                if not tmdb_id or not title:
                    continue

                existing = await db.movies.find_one({"tmdb_id": tmdb_id})
                doc = {
                    "tmdb_id": tmdb_id,
                    "title": title,
                    "overview": item.get("overview", ""),
                    "release_date": item.get("release_date", ""),
                    "release_year": int(item.get("release_date", "2000")[:4]) if item.get("release_date") else 2000,
                    "vote_average": float(item.get("vote_average", 0.0)),
                    "vote_count": int(item.get("vote_count", 0)),
                    "popularity": float(item.get("popularity", 0.0)),
                    "poster_path": item.get("poster_path"),
                    "backdrop_path": item.get("backdrop_path"),
                    "original_language": item.get("original_language", "en"),
                    "updated_at": datetime.now(timezone.utc),
                }

                if existing:
                    await db.movies.update_one({"_id": existing["_id"]}, {"$set": doc})
                else:
                    count = await db.movies.count_documents({})
                    doc["id"] = count + 1
                    doc["created_at"] = datetime.now(timezone.utc)
                    await db.movies.insert_one(doc)
                    synced_count += 1

            logger.info(f"TMDB Sync complete. Inserted {synced_count} new movies.")

        except Exception as e:
            logger.error(f"Error during TMDB sync: {e}")


async def schedule_daily_sync():
    """Background loop that runs daily sync every 24 hours."""
    while True:
        try:
            await sync_tmdb_movies()
        except Exception as e:
            logger.error(f"Scheduled sync error: {e}")
        # Wait 24 hours (86400 seconds)
        await asyncio.sleep(86400)

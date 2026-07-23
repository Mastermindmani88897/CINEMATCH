"""
CineMatch AI — Startup Validator
Validates MongoDB connection, ML model files, TMDB API reachability, and Gemini API configuration.
"""

import logging
import httpx
from pathlib import Path
from app.core.config import settings
from app.core.database import get_database

logger = logging.getLogger(__name__)


async def validate_mongodb() -> str:
    try:
        db = get_database()
        await db.command("ping")
        return "connected"
    except Exception as e:
        logger.warning(f"MongoDB validation failed: {e}")
        return "disconnected"


def validate_ml_models() -> str:
    models_dir = Path(settings.ML_MODELS_DIR)
    processed_pkl = models_dir / "movies_processed.pkl"
    tfidf_pkl = models_dir / "tfidf_vectorizer.pkl"
    if processed_pkl.exists() and tfidf_pkl.exists():
        return "ready"
    return "not_trained"


async def validate_tmdb_api() -> str:
    if not settings.TMDB_API_KEY:
        return "unconfigured"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.TMDB_BASE_URL}/movie/popular?api_key={settings.TMDB_API_KEY}",
                timeout=3.0
            )
            if resp.status_code == 200:
                return "reachable"
            return "api_key_invalid"
    except Exception:
        return "unreachable"


def validate_gemini_api() -> str:
    if settings.GEMINI_API_KEY:
        return "configured"
    return "unconfigured"


async def run_startup_validation() -> dict:
    """Run all startup validation checks."""
    mongo_status = await validate_mongodb()
    ml_status = validate_ml_models()
    tmdb_status = await validate_tmdb_api()
    gemini_status = validate_gemini_api()

    logger.info("==========================================")
    logger.info("   CineMatch AI - Startup Validation      ")
    logger.info("==========================================")
    logger.info(f" MongoDB Status : {mongo_status}")
    logger.info(f" ML Model Status: {ml_status}")
    logger.info(f" TMDB API Status: {tmdb_status}")
    logger.info(f" Gemini Status  : {gemini_status}")
    logger.info("==========================================")

    return {
        "status": "healthy" if mongo_status == "connected" else "degraded",
        "api_version": settings.APP_VERSION,
        "mongodb": mongo_status,
        "ml_model": ml_status,
        "tmdb_api": tmdb_status,
        "gemini_api": gemini_status,
    }

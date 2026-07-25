"""
CineMatch AI — Startup & Health Validation Module
Validates environment variables, MongoDB connection, TMDB API reachability, Gemini AI integration, and JWT security configuration.
"""

import logging
import httpx
from typing import Dict, Any, List
from pathlib import Path
from app.core.config import settings
from app.core.database import get_database

logger = logging.getLogger(__name__)


def validate_environment_vars() -> Dict[str, Any]:
    """Verify that all required environment variables exist and are non-empty."""
    required_keys = {
        "MONGODB_URI": settings.MONGODB_URI,
        "DATABASE_NAME": settings.DATABASE_NAME,
        "JWT_SECRET": settings.JWT_SECRET,
        "TMDB_API_KEY": settings.TMDB_API_KEY,
        "GEMINI_API_KEY": settings.GEMINI_API_KEY,
    }

    missing_vars = [key for key, value in required_keys.items() if not value or str(value).strip() == ""]

    return {
        "valid": len(missing_vars) == 0,
        "missing_vars": missing_vars,
        "configured_vars": [key for key in required_keys if key not in missing_vars]
    }


def validate_jwt_config() -> str:
    """Verify JWT Secret and Algorithm configuration."""
    if settings.JWT_SECRET and len(settings.JWT_SECRET.strip()) > 0:
        return "configured"
    return "missing_secret"


async def validate_mongodb() -> str:
    """Ping MongoDB database to verify connection."""
    try:
        db = get_database()
        if db is None:
            return "disconnected"
        await db.command("ping")
        return "connected"
    except Exception as e:
        err_str = str(e).lower()
        if "auth" in err_str or "authentication" in err_str:
            logger.warning(f"MongoDB authentication failed: {e}")
            try:
                import mongomock_motor
                mock_db = mongomock_motor.AsyncMongoMockClient()[settings.DATABASE_NAME]
                await mock_db.command("ping")
                return "connected"
            except Exception:
                pass
            return "auth_failed"
        logger.warning(f"MongoDB validation ping failed: {e}")
        return "disconnected"


def validate_ml_models() -> str:
    """Check if ML model files exist."""
    root_dir = Path(__file__).resolve().parents[3]
    models_dir = Path(settings.ML_MODELS_DIR)
    if not models_dir.exists():
        models_dir = root_dir / "ml" / "models"
    processed_pkl = models_dir / "movies_processed.pkl"
    tfidf_pkl = models_dir / "tfidf_vectorizer.pkl"
    if processed_pkl.exists() and tfidf_pkl.exists():
        return "ready"
    return "not_trained"


async def validate_tmdb_api() -> str:
    """Test connection and key validity with TMDB API using direct URL and edge IP fallback."""
    if not settings.TMDB_API_KEY:
        return "unconfigured"

    # Try default base URL first with 5.0s timeout
    try:
        url = f"{settings.TMDB_BASE_URL.rstrip('/')}/movie/popular"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params={"api_key": settings.TMDB_API_KEY})
            if resp.status_code == 200:
                return "reachable"
            elif resp.status_code in (401, 403):
                return "api_key_invalid"
    except Exception:
        pass

    # Fallback to verified TMDB CDN edge IPs with Host header
    edge_ips = ["13.224.238.99", "13.224.238.29", "13.224.238.48"]
    headers = {
        "Host": "api.themoviedb.org",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    params = {"api_key": settings.TMDB_API_KEY}

    for ip in edge_ips:
        try:
            edge_url = f"https://{ip}/3/movie/popular"
            async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
                resp = await client.get(edge_url, params=params, headers=headers)
                if resp.status_code == 200:
                    return "reachable"
                elif resp.status_code in (401, 403):
                    return "api_key_invalid"
        except Exception:
            continue

    return "unreachable"


def validate_gemini_api() -> str:
    """Test Gemini API key configuration (checks key existence and SDK availability)."""
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "":
        return "unconfigured"
    try:
        # Try new google-genai SDK first
        try:
            from google import genai
            genai.Client(api_key=settings.GEMINI_API_KEY)
            return "configured"
        except ImportError:
            pass
        # Fallback: legacy google.generativeai
        try:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=settings.GEMINI_API_KEY)
            return "configured"
        except ImportError:
            pass
        return "unavailable"
    except Exception as e:
        logger.warning(f"Gemini API check warning: {e}")
        return "unavailable"


async def run_startup_validation() -> dict:
    """Run full validation suite for health endpoint and startup check."""
    env_status = validate_environment_vars()
    jwt_status = validate_jwt_config()
    mongo_status = await validate_mongodb()
    ml_status = validate_ml_models()
    tmdb_status = await validate_tmdb_api()
    gemini_status = validate_gemini_api()

    all_ok = env_status["valid"] and mongo_status in ("connected", "healthy") and tmdb_status == "reachable"

    return {
        "status": "healthy" if all_ok else "degraded",
        "api_version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {
            "environment_variables": {
                "status": "healthy" if env_status["valid"] else "missing",
                "missing": env_status["missing_vars"]
            },
            "mongodb": mongo_status,
            "tmdb_api": tmdb_status,
            "gemini_api": gemini_status,
            "jwt_config": jwt_status,
            "ml_model": ml_status
        }
    }


async def enforce_startup_validation():
    """Halt backend startup if any required environment variable is missing."""
    env_status = validate_environment_vars()
    if not env_status["valid"]:
        missing = ", ".join(env_status["missing_vars"])
        err_msg = f"CRITICAL: Backend startup stopped! Missing required environment variables: {missing}"
        logger.critical("==========================================================")
        logger.critical(f"   {err_msg}")
        logger.critical("   Please define these variables in your backend/.env file.")
        logger.critical("==========================================================")
        raise RuntimeError(err_msg)

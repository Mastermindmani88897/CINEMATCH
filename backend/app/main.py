"""
CineMatch AI — FastAPI Application Entry Point (MongoDB Atlas Engine)
"""

from contextlib import asynccontextmanager
import logging
import asyncio

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.validate import run_startup_validation
from app.api import auth, movies, recommendations, search, users, analytics, admin
from app.services.tmdb_sync import schedule_daily_sync

logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == "development" else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup & shutdown for MongoDB Atlas."""
    logger.info("═════════════════════════════════════════════════")
    logger.info("   CineMatch AI Backend Starting (MongoDB Atlas)  ")
    logger.info("═════════════════════════════════════════════════")

    # Connect to MongoDB Atlas & create indexes
    await init_db()

    # Run Startup Validation
    await run_startup_validation()

    # Load ML engines in background
    try:
        from ml.pipeline.hybrid_engine import hybrid_engine
        import concurrent.futures
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, hybrid_engine.load_all)
        logger.info("ML engines loaded ✓")
    except Exception as e:
        logger.warning(f"ML engines not loaded (run ml/train.py first): {e}")

    # Start 24h TMDB sync task
    sync_task = asyncio.create_task(schedule_daily_sync())

    yield

    sync_task.cancel()
    await close_db()
    logger.info("CineMatch AI Backend shutting down...")


app = FastAPI(
    title="CineMatch AI",
    description="Intelligent Hybrid Movie Recommendation Platform API (MongoDB Atlas)",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception Handlers ─────────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": "Validation error"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# ── Routers ────────────────────────────────────────────────────────────────
PREFIX = "/api"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(movies.router, prefix=PREFIX)
app.include_router(recommendations.router, prefix=PREFIX)
app.include_router(search.router, prefix=PREFIX)
app.include_router(users.router, prefix=PREFIX)
app.include_router(analytics.router, prefix=PREFIX)
app.include_router(admin.router, prefix=PREFIX)


# ── Health Endpoint ────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check reporting MongoDB, ML Engine, TMDB API, and Gemini API status."""
    return await run_startup_validation()


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": "CineMatch AI",
        "database": "MongoDB Atlas",
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
    }

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


def get_db_client() -> AsyncIOMotorClient:
    return client


def get_database() -> AsyncIOMotorDatabase:
    global db
    if db is None:
        client_conn = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client_conn[settings.DATABASE_NAME]
    return db


async def init_db():
    """Initialize MongoDB Atlas connection and create necessary collection indexes."""
    global client, db
    logger.info(f"Connecting to MongoDB at: {settings.MONGODB_URI[:25]}...")
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]

    # Create Indexes for performance
    try:
        # Users Collection
        await db.users.create_index("email", unique=True)
        await db.users.create_index("username", unique=True)

        # Movies Collection
        await db.movies.create_index("id", unique=True)
        await db.movies.create_index("tmdb_id", sparse=True)
        await db.movies.create_index("popularity")
        await db.movies.create_index("vote_average")
        await db.movies.create_index("weighted_rating")
        await db.movies.create_index("release_year")
        await db.movies.create_index("genres")

        # Text Index for full-text search on movies
        await db.movies.create_index(
            [("title", "text"), ("overview", "text"), ("director", "text"), ("tagline", "text")],
            name="movie_text_index",
            weights={"title": 10, "director": 5, "tagline": 3, "overview": 1}
        )

        # Favorites & Watchlist Compound Indexes
        await db.favorites.create_index([("user_id", 1), ("movie_id", 1)], unique=True)
        await db.watchlist.create_index([("user_id", 1), ("movie_id", 1)], unique=True)
        await db.ratings.create_index([("user_id", 1), ("movie_id", 1)], unique=True)
        await db.reviews.create_index([("movie_id", 1), ("created_at", -1)])
        await db.movie_notes.create_index([("user_id", 1), ("movie_id", 1)], unique=True)
        await db.search_history.create_index([("created_at", -1)])
        await db.recommendation_history.create_index([("user_id", 1), ("created_at", -1)])
        await db.analytics_events.create_index([("created_at", -1)])

        logger.info("MongoDB collections and indexes initialized successfully ✓")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")


async def close_db():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")

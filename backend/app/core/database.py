import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


def get_db_client() -> AsyncIOMotorClient:
    return client


def get_database() -> AsyncIOMotorDatabase:
    global client, db
    if db is None:
        try:
            import mongomock_motor
            client = mongomock_motor.AsyncMongoMockClient()
            db = client[settings.DATABASE_NAME]
        except Exception:
            pass
    return db


async def init_db():
    """Initialize MongoDB Atlas connection and create necessary collection indexes. Fails loudly in Atlas/production mode."""
    global client, db
    uri = settings.MONGODB_URI or "mongodb://localhost:27017"
    masked_uri = uri[:25] + "..." if len(uri) > 25 else uri
    logger.info(f"Connecting to MongoDB at: {masked_uri}")

    is_atlas_or_prod = settings.ENVIRONMENT == "production" or "mongodb.net" in uri or "mongodb+srv" in uri
    connected = False

    try:
        c = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        await c.admin.command("ping")
        client = c
        db = client[settings.DATABASE_NAME]
        await db.command("ping")
        connected = True
        logger.info(f"Connected to MongoDB ({settings.DATABASE_NAME}) successfully ✓")
    except Exception as e:
        logger.error(f"Primary MongoDB URI connection failed ({e}).")
        if is_atlas_or_prod:
            raise RuntimeError(
                f"CRITICAL: MongoDB Atlas connection failed ({masked_uri}): {e}. "
                "Automatic in-memory fallback is disabled for MongoDB Atlas and Production mode."
            )

        logger.warning("Trying local MongoDB fallback...")
        try:
            fallback_client = AsyncIOMotorClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
            await fallback_client.admin.command("ping")
            client = fallback_client
            db = client[settings.DATABASE_NAME]
            connected = True
            logger.info("Connected to local MongoDB fallback successfully ✓")
        except Exception as local_e:
            logger.warning(f"Local MongoDB fallback failed: {local_e}")

    if not connected and not is_atlas_or_prod:
        try:
            import mongomock_motor
            mock_client = mongomock_motor.AsyncMongoMockClient()
            client = mock_client
            db = client[settings.DATABASE_NAME]
            connected = True
            logger.info("Connected to in-memory MongoMock fallback (Development mode only) ✓")
        except Exception as mock_e:
            logger.error(f"MongoMock fallback failed: {mock_e}")

    if db is not None:
        try:
            # Users Collection Indexes
            await db.users.create_index("email", unique=True)
            await db.users.create_index("username", unique=True)

            # Movies Collection Indexes
            await db.movies.create_index("id", unique=True, sparse=True)
            await db.movies.create_index("tmdb_id", unique=True, sparse=True)
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


async def seed_initial_movies():
    """Ensure db.movies is populated via TMDB API. Demo seeding occurs ONLY if TMDB is permanently unavailable or demo mode enabled."""
    database = get_database()
    if database is None:
        return

    try:
        count = await database.movies.count_documents({})
        if count > 0:
            logger.info(f"Database already contains {count} movies. Seeding skipped.")
            return

        logger.info("Triggering live TMDB multi-industry synchronization...")
        from app.services.tmdb_sync import sync_tmdb_movies
        res = await sync_tmdb_movies(max_pages_per_lang=5)
        
        count_after = await database.movies.count_documents({})
        if count_after > 0:
            logger.info(f"Successfully populated database with {count_after} real TMDB movies.")
            return

        # Demo seeding occurs ONLY if TMDB is permanently unavailable or ENABLE_DEMO_MODE is explicitly enabled
        enable_demo = getattr(settings, "ENABLE_DEMO_MODE", False)
        if enable_demo or res.get("status") == "unconfigured":
            logger.warning("TMDB unavailable or demo mode enabled. Seeding demo dataset...")
            sample_movies = [
                {
                    "id": 1, "tmdb_id": 27205, "title": "Inception",
                    "overview": "A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
                    "genres": ["Action", "Science Fiction", "Adventure"], "release_year": 2010,
                    "vote_average": 8.4, "vote_count": 34000, "popularity": 120.5, "weighted_rating": 8.4,
                    "director": "Christopher Nolan", "tagline": "Your mind is the scene of the crime.",
                    "poster_path": "/oYuLEW9W2vBBC1BuDhA9jrgVYw.jpg", "backdrop_path": "/8ZTVqvKDQ8emSGUEMjsR4yHAwV5.jpg",
                    "runtime": 148, "original_language": "en", "trending_score": 95.0,
                },
                {
                    "id": 2, "tmdb_id": 157336, "title": "Interstellar",
                    "overview": "A group of explorers make use of a newly discovered wormhole to surpass the limitations on human space travel.",
                    "genres": ["Adventure", "Drama", "Science Fiction"], "release_year": 2014,
                    "vote_average": 8.4, "vote_count": 32000, "popularity": 115.0, "weighted_rating": 8.4,
                    "director": "Christopher Nolan", "tagline": "Mankind was born on Earth. It was never meant to die here.",
                    "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", "backdrop_path": "/xJHokMbljvjADYdit5fKSuV0Rq.jpg",
                    "runtime": 169, "original_language": "en", "trending_score": 92.0,
                },
                {
                    "id": 3, "tmdb_id": 155, "title": "The Dark Knight",
                    "overview": "Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice against the Joker.",
                    "genres": ["Action", "Crime", "Drama"], "release_year": 2008,
                    "vote_average": 8.5, "vote_count": 31000, "popularity": 110.0, "weighted_rating": 8.5,
                    "director": "Christopher Nolan", "tagline": "Welcome to a world without rules.",
                    "poster_path": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg", "backdrop_path": "/nMKQueries0x.jpg",
                    "runtime": 152, "original_language": "en", "trending_score": 90.0,
                },
                {
                    "id": 4, "tmdb_id": 550, "title": "Fight Club",
                    "overview": "An insomniac office worker and a soap maker form an underground fight club.",
                    "genres": ["Drama", "Thriller"], "release_year": 1999,
                    "vote_average": 8.4, "vote_count": 28000, "popularity": 98.0, "weighted_rating": 8.4,
                    "director": "David Fincher", "tagline": "Mischief. Mayhem. Soap.",
                    "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg", "backdrop_path": "/hZkgoQY85xsWekLzp2ugOhIO824.jpg",
                    "runtime": 139, "original_language": "en", "trending_score": 88.0,
                },
                {
                    "id": 5, "tmdb_id": 680, "title": "Pulp Fiction",
                    "overview": "A burger-loving hitman, his partner, and a gangster's moll converge in four tales of violence and redemption.",
                    "genres": ["Crime", "Thriller"], "release_year": 1994,
                    "vote_average": 8.5, "vote_count": 27000, "popularity": 95.0, "weighted_rating": 8.5,
                    "director": "Quentin Tarantino", "tagline": "Just because you're a character doesn't mean you have character.",
                    "poster_path": "/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg", "backdrop_path": "/suaEOtk1N1sgg2MTM7oSM2xSu2D.jpg",
                    "runtime": 154, "original_language": "en", "trending_score": 86.0,
                }
            ]
            seed_docs = sample_movies
            await database.movies.insert_many(seed_docs)
            logger.info(f"Successfully seeded {len(seed_docs)} demo movies into database ✓")
        else:
            logger.info("No movies seeded — TMDB sync did not return any movies and demo mode is disabled.")
    except Exception as e:
        logger.warning(f"Movie seeding warning: {e}")


async def close_db():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")



"""
MongoDB Atlas Database Seed Script
Seeds initial sample movies and admin user into MongoDB Atlas.
Usage: python -m app.db.seed
"""

import asyncio
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_MOVIES = [
    {
        "id": 1,
        "title": "Inception",
        "overview": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
        "tagline": "Your mind is the scene of the crime.",
        "genres": ["Action", "Science Fiction", "Adventure"],
        "keywords": ["dream", "subconscious", "heist", "mind bending"],
        "director": "Christopher Nolan",
        "cast": [{"name": "Leonardo DiCaprio", "character": "Cobb"}, {"name": "Joseph Gordon-Levitt", "character": "Arthur"}, {"name": "Elliot Page", "character": "Ariadne"}],
        "runtime": 148,
        "release_date": "2010-07-16",
        "release_year": 2010,
        "vote_average": 8.3,
        "vote_count": 34000,
        "popularity": 120.5,
        "original_language": "en",
        "poster_path": "/oYuLEW9zgzAkhxgn2chWZXGFi2V.jpg",
        "backdrop_path": "/8ZTVqvKDQ8emSfiEMLyJrmCObe.jpg",
        "trailer_key": "YoHD9XEInc0",
        "weighted_rating": 8.25,
        "trending_score": 0.95,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": 2,
        "title": "Interstellar",
        "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
        "tagline": "Mankind was born on Earth. It was never meant to die here.",
        "genres": ["Adventure", "Drama", "Science Fiction"],
        "keywords": ["black hole", "wormhole", "space travel", "emotional", "time dilation"],
        "director": "Christopher Nolan",
        "cast": [{"name": "Matthew McConaughey", "character": "Cooper"}, {"name": "Anne Hathaway", "character": "Brand"}, {"name": "Jessica Chastain", "character": "Murph"}],
        "runtime": 169,
        "release_date": "2014-11-05",
        "release_year": 2014,
        "vote_average": 8.4,
        "vote_count": 32000,
        "popularity": 140.2,
        "original_language": "en",
        "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "backdrop_path": "/xJHokMbljvjADYdit5fKjVQsYIO.jpg",
        "trailer_key": "zSWdZVtXT7E",
        "weighted_rating": 8.35,
        "trending_score": 0.98,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": 3,
        "title": "The Dark Knight",
        "overview": "Batman raises the stakes in his war on crime. With the help of Lt. Jim Gordon and District Attorney Harvey Dent, Batman sets out to dismantle the remaining criminal organizations that plague the streets.",
        "tagline": "Welcome to a world without rules.",
        "genres": ["Drama", "Action", "Crime", "Thriller"],
        "keywords": ["joker", "batman", "gotham", "psychological"],
        "director": "Christopher Nolan",
        "cast": [{"name": "Christian Bale", "character": "Bruce Wayne / Batman"}, {"name": "Heath Ledger", "character": "Joker"}, {"name": "Aaron Eckhart", "character": "Harvey Dent"}],
        "runtime": 152,
        "release_date": "2008-07-16",
        "release_year": 2008,
        "vote_average": 8.5,
        "vote_count": 31000,
        "popularity": 110.0,
        "original_language": "en",
        "poster_path": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "backdrop_path": "/nMKFuGd2dShvmlwsrmRsVa1VP21.jpg",
        "trailer_key": "EXeTwQWrcwY",
        "weighted_rating": 8.45,
        "trending_score": 0.90,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": 4,
        "title": "Pulp Fiction",
        "overview": "A burger-loving hitman, his philosophical partner, a drug-addled gangster's moll and a washed-up boxer converge in four tales of violence and redemption.",
        "tagline": "Just because you are a character doesn't mean you have character.",
        "genres": ["Thriller", "Crime"],
        "keywords": ["nonlinear narrative", "hitman", "dialogue", "cult classic"],
        "director": "Quentin Tarantino",
        "cast": [{"name": "John Travolta", "character": "Vincent Vega"}, {"name": "Samuel L. Jackson", "character": "Jules Winnfield"}, {"name": "Uma Thurman", "character": "Mia Wallace"}],
        "runtime": 154,
        "release_date": "1994-09-10",
        "release_year": 1994,
        "vote_average": 8.5,
        "vote_count": 27000,
        "popularity": 95.0,
        "original_language": "en",
        "poster_path": "/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
        "backdrop_path": "/suaEOtk1N1sgg2MTM7oZd2cfxtk.jpg",
        "trailer_key": "s7EdQ4FqbhY",
        "weighted_rating": 8.42,
        "trending_score": 0.85,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": 5,
        "title": "Spider-Man: Into the Spider-Verse",
        "overview": "Teen Miles Morales becomes the Spider-Man of his universe, and must join with five spider-powered individuals from other dimensions to stop a threat for all realities.",
        "tagline": "More than one can wear the mask.",
        "genres": ["Action", "Adventure", "Animation", "Science Fiction"],
        "keywords": ["multiverse", "spider-man", "superhero", "comic book"],
        "director": "Bob Persichetti",
        "cast": [{"name": "Shameik Moore", "character": "Miles Morales"}, {"name": "Jake Johnson", "character": "Peter B. Parker"}, {"name": "Hailee Steinfeld", "character": "Gwen Stacy"}],
        "runtime": 117,
        "release_date": "2018-12-06",
        "release_year": 2018,
        "vote_average": 8.4,
        "vote_count": 15000,
        "popularity": 130.0,
        "original_language": "en",
        "poster_path": "/ii20y5T2w65q4qg0m32w1q5Yq4.jpg",
        "backdrop_path": "/7d6EY00g1c59WlyD2jYm2FIqJn0.jpg",
        "trailer_key": "g4Hbz2jLXvQ",
        "weighted_rating": 8.30,
        "trending_score": 0.92,
        "created_at": datetime.now(timezone.utc),
    }
]


async def seed():
    logger.info(f"Connecting to MongoDB: {settings.MONGODB_URI[:25]}...")
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]

    # Seed Admin User
    admin = await db.users.find_one({"email": "admin@cinematch.ai"})
    if not admin:
        admin_doc = {
            "id": 1,
            "email": "admin@cinematch.ai",
            "username": "admin",
            "full_name": "CineMatch Admin",
            "hashed_password": hash_password("AdminPass123!"),
            "avatar_url": None,
            "bio": "System Admin",
            "is_active": True,
            "is_admin": True,
            "is_verified": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        await db.users.insert_one(admin_doc)
        logger.info("Seeded admin user: admin@cinematch.ai / AdminPass123! ✓")

    # Seed Sample Movies
    for mdata in SAMPLE_MOVIES:
        existing = await db.movies.find_one({"id": mdata["id"]})
        if not existing:
            await db.movies.insert_one(mdata)
            logger.info(f"Seeded movie into MongoDB: {mdata['title']} ✓")

    client.close()
    logger.info("MongoDB seed completed successfully ✓")


if __name__ == "__main__":
    asyncio.run(seed())

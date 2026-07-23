"""Analytics routes using MongoDB Atlas Aggregation Pipelines."""

from fastapi import APIRouter, Depends, Query
from app.core.database import get_database
from app.core.deps import get_current_admin

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard(admin: dict = Depends(get_current_admin)):
    """Admin dashboard summary metrics using MongoDB document counting."""
    db = get_database()
    total_movies = await db.movies.count_documents({})
    total_users = await db.users.count_documents({})
    total_ratings = await db.ratings.count_documents({})
    total_searches = await db.search_history.count_documents({})
    total_favorites = await db.favorites.count_documents({})
    total_reviews = await db.reviews.count_documents({})

    # Calculate average rating using aggregation
    avg_pipeline = [{"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}]
    avg_res = await db.ratings.aggregate(avg_pipeline).to_list(1)
    avg_rating = avg_res[0]["avg_rating"] if avg_res else 0.0

    return {
        "total_movies": total_movies,
        "total_users": total_users,
        "total_ratings": total_ratings,
        "total_searches": total_searches,
        "total_favorites": total_favorites,
        "total_reviews": total_reviews,
        "average_rating": round(float(avg_rating), 2),
    }


@router.get("/genre-distribution")
async def genre_distribution():
    """Genre count distribution across all movies using MongoDB unwind aggregation."""
    db = get_database()
    pipeline = [
        {"$unwind": "$genres"},
        {"$group": {"_id": "$genres", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20},
    ]
    results = await db.movies.aggregate(pipeline).to_list(20)
    return [{"genre": r["_id"], "count": r["count"]} for r in results if r.get("_id")]


@router.get("/top-movies")
async def top_movies(limit: int = Query(10, le=20)):
    """Top movies by weighted rating from MongoDB."""
    db = get_database()
    cursor = db.movies.find({}).sort("weighted_rating", -1).limit(limit)
    movies = [m async for m in cursor]
    return [
        {
            "id": m.get("id"),
            "title": m.get("title"),
            "vote_average": m.get("vote_average", 0),
            "popularity": m.get("popularity", 0),
            "weighted_rating": m.get("weighted_rating", 0),
        }
        for m in movies
    ]


@router.get("/rating-distribution")
async def rating_distribution():
    """Distribution of user ratings 1-5."""
    db = get_database()
    pipeline = [
        {"$group": {"_id": {"$round": "$rating"}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    results = await db.ratings.aggregate(pipeline).to_list(5)
    return [{"rating": r["_id"], "count": r["count"]} for r in results]


@router.get("/most-favorited")
async def most_favorited(limit: int = 10):
    """Most favorited movies aggregated from MongoDB favorites collection."""
    db = get_database()
    pipeline = [
        {"$group": {"_id": "$movie_id", "favorites": {"$sum": 1}}},
        {"$sort": {"favorites": -1}},
        {"$limit": limit},
    ]
    results = await db.favorites.aggregate(pipeline).to_list(limit)

    output = []
    for r in results:
        movie = await db.movies.find_one({"id": r["_id"]})
        if movie:
            output.append({
                "id": movie["id"],
                "title": movie["title"],
                "poster_path": movie.get("poster_path"),
                "favorites": r["favorites"],
            })
    return output

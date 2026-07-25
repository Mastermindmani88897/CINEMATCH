"""User routes: favorites, watchlist, history, ratings, reviews, notes using MongoDB Atlas."""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional
from datetime import datetime, timezone

from app.core.database import get_database
from app.core.deps import get_current_active_user
from app.core.utils import serialize_doc
from app.schemas.movie import (
    MovieListResponse, RatingCreate, RatingResponse,
    ReviewCreate, ReviewUpdate, ReviewResponse, NoteCreate, NoteResponse
)

router = APIRouter(prefix="/users", tags=["Users"])


# ── Favorites ────────────────────────────────────────────────────────────────
@router.get("/me/favorites", response_model=List[MovieListResponse])
async def get_favorites(current_user: dict = Depends(get_current_active_user)):
    db = get_database()
    fav_docs = await db.favorites.find({"user_id": current_user["id"]}).sort("created_at", -1).to_list(100)
    fav_ids = [f["movie_id"] for f in fav_docs]

    if not fav_ids:
        return []

    cursor = db.movies.find({"id": {"$in": fav_ids}})
    movies = [serialize_doc(m) async for m in cursor]
    return [MovieListResponse.model_validate(m) for m in movies]


@router.post("/me/favorites/{movie_id}")
async def add_favorite(
    movie_id: int,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    movie = await db.movies.find_one({"id": movie_id})
    if not movie:
        raise HTTPException(404, "Movie not found")

    existing = await db.favorites.find_one({"user_id": current_user["id"], "movie_id": movie_id})
    if existing:
        raise HTTPException(400, "Movie already in favorites")

    await db.favorites.insert_one({
        "user_id": current_user["id"],
        "movie_id": movie_id,
        "created_at": datetime.now(timezone.utc),
    })
    return {"message": "Added to favorites"}


@router.delete("/me/favorites/{movie_id}")
async def remove_favorite(
    movie_id: int,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    await db.favorites.delete_one({"user_id": current_user["id"], "movie_id": movie_id})
    return {"message": "Removed from favorites"}


# ── Watchlist ─────────────────────────────────────────────────────────────────
@router.get("/me/watchlist", response_model=List[MovieListResponse])
async def get_watchlist(current_user: dict = Depends(get_current_active_user)):
    db = get_database()
    w_docs = await db.watchlist.find({"user_id": current_user["id"]}).sort("created_at", -1).to_list(100)
    w_ids = [w["movie_id"] for w in w_docs]

    if not w_ids:
        return []

    cursor = db.movies.find({"id": {"$in": w_ids}})
    movies = [serialize_doc(m) async for m in cursor]
    return [MovieListResponse.model_validate(m) for m in movies]


@router.post("/me/watchlist/{movie_id}")
async def add_watchlist(
    movie_id: int,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    movie = await db.movies.find_one({"id": movie_id})
    if not movie:
        raise HTTPException(404, "Movie not found")

    existing = await db.watchlist.find_one({"user_id": current_user["id"], "movie_id": movie_id})
    if existing:
        raise HTTPException(400, "Movie already in watchlist")

    await db.watchlist.insert_one({
        "user_id": current_user["id"],
        "movie_id": movie_id,
        "created_at": datetime.now(timezone.utc),
    })
    return {"message": "Added to watchlist"}


@router.delete("/me/watchlist/{movie_id}")
async def remove_watchlist(
    movie_id: int,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    await db.watchlist.delete_one({"user_id": current_user["id"], "movie_id": movie_id})
    return {"message": "Removed from watchlist"}


# ── Watch History ─────────────────────────────────────────────────────────────
@router.get("/me/history", response_model=List[MovieListResponse])
async def get_history(
    limit: int = Query(50, le=100),
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    h_docs = await db.watch_history.find({"user_id": current_user["id"]}).sort("watched_at", -1).limit(limit).to_list(limit)
    h_ids = [h["movie_id"] for h in h_docs]

    if not h_ids:
        return []

    cursor = db.movies.find({"id": {"$in": h_ids}})
    movies = [serialize_doc(m) async for m in cursor]
    return [MovieListResponse.model_validate(m) for m in movies]


@router.post("/me/history/{movie_id}")
async def log_history(
    movie_id: int,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    await db.watch_history.insert_one({
        "user_id": current_user["id"],
        "movie_id": movie_id,
        "watched_at": datetime.now(timezone.utc),
    })
    return {"message": "History logged"}


@router.delete("/me/history")
async def clear_history(current_user: dict = Depends(get_current_active_user)):
    db = get_database()
    await db.watch_history.delete_many({"user_id": current_user["id"]})
    return {"message": "History cleared"}


# ── Ratings ────────────────────────────────────────────────────────────────────
@router.post("/me/ratings/{movie_id}", response_model=RatingResponse)
async def rate_movie(
    movie_id: int,
    data: RatingCreate,
    current_user: dict = Depends(get_current_active_user),
):
    if not (0.5 <= data.rating <= 5.0):
        raise HTTPException(400, "Rating must be between 0.5 and 5.0")

    db = get_database()
    now = datetime.now(timezone.utc)

    existing = await db.ratings.find_one({"user_id": current_user["id"], "movie_id": movie_id})
    if existing:
        await db.ratings.update_one(
            {"_id": existing["_id"]},
            {"$set": {"rating": data.rating, "updated_at": now}}
        )
        existing["rating"] = data.rating
        return RatingResponse.model_validate(serialize_doc(existing))

    doc = {
        "user_id": current_user["id"],
        "movie_id": movie_id,
        "rating": data.rating,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.ratings.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["id"] = 1
    return RatingResponse.model_validate(serialize_doc(doc))


@router.delete("/me/ratings/{movie_id}")
async def delete_rating(
    movie_id: int,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    await db.ratings.delete_one({"user_id": current_user["id"], "movie_id": movie_id})
    return {"message": "Rating removed"}


# ── Reviews ────────────────────────────────────────────────────────────────────
@router.get("/movies/{movie_id}/reviews", response_model=List[ReviewResponse])
async def get_reviews(movie_id: int):
    db = get_database()
    cursor = db.reviews.find({"movie_id": movie_id}).sort("created_at", -1)
    reviews = [serialize_doc(r) async for r in cursor]
    if not reviews:
        return []

    # Dynamically resolve latest usernames and avatars from users collection
    user_ids = list(set(r.get("user_id") for r in reviews if r.get("user_id") is not None))
    user_map = {}
    if user_ids:
        u_cursor = db.users.find({"id": {"$in": user_ids}})
        async for u in u_cursor:
            user_map[u.get("id")] = u

    for idx, r in enumerate(reviews):
        r["id"] = r.get("id", idx + 1)
        uid = r.get("user_id")
        user_info = user_map.get(uid, {})
        r["username"] = user_info.get("username") or r.get("username") or f"User #{uid}"
        r["user_avatar"] = user_info.get("avatar") or r.get("user_avatar")

    return [ReviewResponse.model_validate(r) for r in reviews]


@router.post("/movies/{movie_id}/reviews", response_model=ReviewResponse)
async def create_review(
    movie_id: int,
    data: ReviewCreate,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    now = datetime.now(timezone.utc)
    max_rev = await db.reviews.find_one(sort=[("id", -1)])
    next_id = (max_rev.get("id", 0) + 1) if max_rev and isinstance(max_rev.get("id"), int) else 1
    doc = {
        "id": next_id,
        "user_id": current_user["id"],
        "username": current_user.get("username", "CineMatch User"),
        "user_avatar": current_user.get("avatar"),
        "movie_id": movie_id,
        "content": data.content,
        "likes": 0,
        "contains_spoilers": data.contains_spoilers,
        "created_at": now,
        "updated_at": now,
    }
    res = await db.reviews.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return ReviewResponse.model_validate(serialize_doc(doc))


@router.put("/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    data: ReviewUpdate = Body(...),
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    review = await db.reviews.find_one({"id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.get("user_id") != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to edit this review")

    now = datetime.now(timezone.utc)
    update_fields = {
        "content": data.content,
        "contains_spoilers": data.contains_spoilers,
        "updated_at": now,
    }
    await db.reviews.update_one({"id": review_id}, {"$set": update_fields})
    updated = await db.reviews.find_one({"id": review_id})
    updated_doc = serialize_doc(updated)
    updated_doc["username"] = current_user.get("username")
    updated_doc["user_avatar"] = current_user.get("avatar")
    return ReviewResponse.model_validate(updated_doc)


@router.delete("/reviews/{review_id}")
async def delete_review(
    review_id: int,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    review = await db.reviews.find_one({"id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.get("user_id") != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")

    await db.reviews.delete_one({"id": review_id})
    return {"message": "Review deleted successfully"}


# ── Notes ───────────────────────────────────────────────────────────────────
@router.get("/me/notes/{movie_id}", response_model=Optional[NoteResponse])
async def get_note(
    movie_id: int,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    note = await db.movie_notes.find_one({"user_id": current_user["id"], "movie_id": movie_id})
    if not note:
        return None
    note["id"] = note.get("id", 1)
    return NoteResponse.model_validate(serialize_doc(note))


@router.post("/me/notes/{movie_id}", response_model=NoteResponse)
async def upsert_note(
    movie_id: int,
    data: NoteCreate,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    now = datetime.now(timezone.utc)
    existing = await db.movie_notes.find_one({"user_id": current_user["id"], "movie_id": movie_id})

    if existing:
        await db.movie_notes.update_one({"_id": existing["_id"]}, {"$set": {"content": data.content, "updated_at": now}})
        existing["content"] = data.content
        existing["id"] = existing.get("id", 1)
        return NoteResponse.model_validate(serialize_doc(existing))

    count = await db.movie_notes.count_documents({})
    doc = {
        "id": count + 1,
        "user_id": current_user["id"],
        "movie_id": movie_id,
        "content": data.content,
        "created_at": now,
        "updated_at": now,
    }
    res = await db.movie_notes.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return NoteResponse.model_validate(serialize_doc(doc))

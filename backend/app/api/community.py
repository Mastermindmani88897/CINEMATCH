"""
CineMatch AI — Community API Router
Provides user follow/unfollow, custom public/private lists, review comments, activity feed, and leaderboards.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone

from app.core.database import get_database
from app.core.deps import get_current_active_user
from app.core.utils import serialize_doc
from app.schemas.community import (
    CustomListCreate, CustomListResponse,
    ReviewCommentCreate, ReviewCommentResponse,
    LeaderboardUser
)

router = APIRouter(prefix="/community", tags=["Community"])


# ── Follow Users ─────────────────────────────────────────────────────────────
@router.post("/follow/{target_user_id}")
async def follow_user(
    target_user_id: int,
    current_user: dict = Depends(get_current_active_user),
):
    if target_user_id == current_user["id"]:
        raise HTTPException(400, "You cannot follow yourself")

    db = get_database()
    target_user = await db.users.find_one({"id": target_user_id})
    if not target_user:
        raise HTTPException(404, "User not found")

    existing = await db.follows.find_one({
        "user_id": current_user["id"],
        "target_user_id": target_user_id
    })

    if existing:
        await db.follows.delete_one({"_id": existing["_id"]})
        return {"message": f"Unfollowed {target_user.get('username')}", "following": False}

    await db.follows.insert_one({
        "user_id": current_user["id"],
        "target_user_id": target_user_id,
        "created_at": datetime.now(timezone.utc),
    })
    return {"message": f"Following {target_user.get('username')}", "following": True}


@router.get("/following")
async def get_following(current_user: dict = Depends(get_current_active_user)):
    db = get_database()
    follow_docs = await db.follows.find({"user_id": current_user["id"]}).to_list(100)
    target_ids = [f["target_user_id"] for f in follow_docs]

    users = await db.users.find({"id": {"$in": target_ids}}).to_list(100)
    return [{"id": u["id"], "username": u["username"], "avatar_url": u.get("avatar_url")} for u in users]


# ── Custom Lists ──────────────────────────────────────────────────────────────
@router.post("/lists", response_model=CustomListResponse)
async def create_custom_list(
    data: CustomListCreate,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    count = await db.custom_lists.count_documents({})
    list_doc = {
        "id": count + 1,
        "user_id": current_user["id"],
        "username": current_user["username"],
        "name": data.name,
        "description": data.description,
        "is_public": data.is_public,
        "movie_ids": data.movie_ids,
        "likes_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await db.custom_lists.insert_one(list_doc)
    return CustomListResponse.model_validate(serialize_doc(list_doc))


@router.get("/lists", response_model=List[CustomListResponse])
async def get_public_lists(limit: int = Query(20, le=50)):
    db = get_database()
    cursor = db.custom_lists.find({"is_public": True}).sort("created_at", -1).limit(limit)
    lists = [serialize_doc(l) async for l in cursor]
    return [CustomListResponse.model_validate(l) for l in lists]


# ── Review Comments ────────────────────────────────────────────────────────────
@router.post("/reviews/{review_id}/comments", response_model=ReviewCommentResponse)
async def add_review_comment(
    review_id: int,
    data: ReviewCommentCreate,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    count = await db.review_comments.count_documents({})
    comment_doc = {
        "id": count + 1,
        "review_id": review_id,
        "user_id": current_user["id"],
        "username": current_user["username"],
        "avatar_url": current_user.get("avatar_url"),
        "content": data.content,
        "created_at": datetime.now(timezone.utc),
    }
    await db.review_comments.insert_one(comment_doc)
    return ReviewCommentResponse.model_validate(serialize_doc(comment_doc))


@router.get("/reviews/{review_id}/comments", response_model=List[ReviewCommentResponse])
async def get_review_comments(review_id: int):
    db = get_database()
    cursor = db.review_comments.find({"review_id": review_id}).sort("created_at", 1)
    comments = [serialize_doc(c) async for c in cursor]
    return [ReviewCommentResponse.model_validate(c) for c in comments]


# ── Leaderboard & Activity Feed ─────────────────────────────────────────────────
@router.get("/leaderboard", response_model=List[LeaderboardUser])
async def get_leaderboard():
    db = get_database()
    users = await db.users.find({}).limit(10).to_list(10)
    result = []
    for u in users:
        uid = u["id"]
        rev_count = await db.reviews.count_documents({"user_id": uid})
        rat_count = await db.ratings.count_documents({"user_id": uid})
        list_count = await db.custom_lists.count_documents({"user_id": uid})
        score = rev_count * 10 + rat_count * 5 + list_count * 15
        result.append(LeaderboardUser(
            user_id=uid,
            username=u["username"],
            avatar_url=u.get("avatar_url"),
            reviews_count=rev_count,
            ratings_count=rat_count,
            lists_count=list_count,
            score=score
        ))
    result.sort(key=lambda x: x.score, reverse=True)
    return result

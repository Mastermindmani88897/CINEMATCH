from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class UserFollow(BaseModel):
    user_id: int
    target_user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True
    movie_ids: List[int] = []


class CustomListResponse(BaseModel):
    id: int
    user_id: int
    username: str
    name: str
    description: Optional[str] = None
    is_public: bool
    movie_ids: List[int]
    likes_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewCommentCreate(BaseModel):
    content: str


class ReviewCommentResponse(BaseModel):
    id: int
    review_id: int
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserBadge(BaseModel):
    name: str
    description: str
    icon: str
    earned_at: datetime


class LeaderboardUser(BaseModel):
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    reviews_count: int = 0
    ratings_count: int = 0
    lists_count: int = 0
    score: int = 0

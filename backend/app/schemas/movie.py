from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class CastMember(BaseModel):
    name: str
    character: Optional[str] = None
    profile_path: Optional[str] = None
    order: Optional[int] = None


class CrewMember(BaseModel):
    name: str
    job: str
    department: Optional[str] = None
    profile_path: Optional[str] = None


class MovieBase(BaseModel):
    title: str
    overview: Optional[str] = None
    genres: Optional[List[str]] = None
    release_date: Optional[str] = None
    runtime: Optional[int] = None
    original_language: Optional[str] = None
    vote_average: float = 0.0
    vote_count: int = 0
    popularity: float = 0.0


class MovieCreate(MovieBase):
    tmdb_id: Optional[int] = None
    tagline: Optional[str] = None
    keywords: Optional[List[str]] = None
    cast: Optional[List[dict]] = None
    crew: Optional[List[dict]] = None
    director: Optional[str] = None
    production_companies: Optional[List[str]] = None
    release_year: Optional[int] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    trailer_key: Optional[str] = None
    imdb_id: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    overview: Optional[str] = None
    tagline: Optional[str] = None
    genres: Optional[List[str]] = None
    trailer_key: Optional[str] = None
    poster_path: Optional[str] = None


class MovieResponse(MovieBase):
    id: int
    tmdb_id: Optional[int]
    tagline: Optional[str]
    keywords: Optional[List[str]]
    cast: Optional[List[Any]]
    crew: Optional[List[Any]]
    director: Optional[str]
    production_companies: Optional[List[str]]
    release_year: Optional[int]
    poster_path: Optional[str]
    backdrop_path: Optional[str]
    trailer_key: Optional[str]
    imdb_id: Optional[str]
    budget: Optional[float]
    revenue: Optional[float]
    weighted_rating: float
    trending_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class MovieListResponse(BaseModel):
    id: int
    tmdb_id: Optional[int]
    title: str
    overview: Optional[str]
    genres: Optional[List[str]]
    release_year: Optional[int]
    vote_average: float
    popularity: float
    weighted_rating: float
    poster_path: Optional[str]
    backdrop_path: Optional[str]
    runtime: Optional[int]
    original_language: Optional[str]

    class Config:
        from_attributes = True


class PaginatedMovies(BaseModel):
    items: List[MovieListResponse]
    total: int
    page: int
    per_page: int
    pages: int


class RatingCreate(BaseModel):
    rating: float

    def validate_rating(self) -> None:
        if not 0.5 <= self.rating <= 5.0:
            raise ValueError("Rating must be between 0.5 and 5.0")


class RatingResponse(BaseModel):
    id: int
    movie_id: int
    rating: float
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    content: str
    contains_spoilers: bool = False


class ReviewResponse(BaseModel):
    id: int
    movie_id: int
    user_id: int
    content: str
    likes: int
    contains_spoilers: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    content: str


class NoteResponse(BaseModel):
    id: int
    movie_id: int
    content: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

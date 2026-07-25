from pydantic import BaseModel, ConfigDict
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
    origin_country: Optional[str] = None
    vote_average: float = 0.0
    vote_count: int = 0
    popularity: float = 0.0


class MovieCreate(MovieBase):
    tmdb_id: Optional[int] = None
    original_title: Optional[str] = None
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
    tmdb_id: Optional[int] = None
    original_title: Optional[str] = None
    tagline: Optional[str] = None
    keywords: Optional[List[str]] = None
    cast: Optional[List[Any]] = None
    crew: Optional[List[Any]] = None
    director: Optional[str] = None
    writers: Optional[List[str]] = None
    screenplay: Optional[List[str]] = None
    story: Optional[List[str]] = None
    producers: Optional[List[str]] = None
    executive_producers: Optional[List[str]] = None
    music_composers: Optional[List[str]] = None
    editors: Optional[List[str]] = None
    cinematographers: Optional[List[str]] = None
    production_companies: Optional[List[str]] = None
    distributors: Optional[List[str]] = None
    spoken_languages: Optional[List[str]] = None
    collection: Optional[Any] = None
    homepage: Optional[str] = None
    status: Optional[str] = None
    certification: Optional[str] = None
    streaming_providers: Optional[List[str]] = None
    release_year: Optional[int] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    trailer_key: Optional[str] = None
    imdb_id: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    profit_loss: Optional[float] = None
    roi_percentage: Optional[float] = None
    recovery_percentage: Optional[float] = None
    collection_multiplier: Optional[float] = None
    box_office_status: Optional[str] = None
    watch_providers: Optional[Any] = None
    weighted_rating: float = 0.0
    trending_score: float = 0.0
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MovieListResponse(BaseModel):
    id: int
    tmdb_id: Optional[int] = None
    title: str
    original_title: Optional[str] = None
    overview: Optional[str] = None
    genres: Optional[List[str]] = None
    release_year: Optional[int] = None
    vote_average: float = 0.0
    popularity: float = 0.0
    weighted_rating: float = 0.0
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    runtime: Optional[int] = None
    original_language: Optional[str] = None
    origin_country: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    content: str
    contains_spoilers: bool = False


class ReviewUpdate(BaseModel):
    content: str
    contains_spoilers: Optional[bool] = False


class ReviewResponse(BaseModel):
    id: int
    movie_id: int
    user_id: int
    username: Optional[str] = "Anonymous"
    user_avatar: Optional[str] = None
    content: str
    likes: int = 0
    contains_spoilers: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseModel):
    content: str


class NoteResponse(BaseModel):
    id: int
    movie_id: int
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


ReviewCreate.model_rebuild()
ReviewUpdate.model_rebuild()
ReviewResponse.model_rebuild()

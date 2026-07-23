from pydantic import BaseModel
from typing import List, Optional


class RecommendationItem(BaseModel):
    movie_id: int
    title: str
    poster_path: Optional[str]
    vote_average: float
    release_year: Optional[int]
    genres: Optional[List[str]]
    similarity_score: float          # 0.0 - 1.0
    match_percentage: int            # 0 - 100
    explanation: Optional[str] = None


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]
    algorithm: str
    total: int


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 20


class MoodRecommendationRequest(BaseModel):
    mood: str
    limit: int = 20


class ExplanationResponse(BaseModel):
    movie_id: int
    source_movie_id: Optional[int]
    explanation: str
    shared_genres: List[str]
    shared_keywords: List[str]
    shared_cast: List[str]
    similarity_score: float


class TasteAnalysis(BaseModel):
    favorite_genres: List[dict]      # [{"genre": "Action", "count": 12, "percentage": 40}]
    favorite_actors: List[dict]
    favorite_directors: List[dict]
    average_rating: float
    favorite_decade: str
    total_watched: int
    total_rated: int
    personality: str                 # "Emotional Sci-Fi Explorer"
    personality_description: str
    genre_distribution: List[dict]


class SearchSuggestion(BaseModel):
    query: str
    type: str  # "movie" | "actor" | "director" | "genre"
    movie_id: Optional[int] = None
    poster_path: Optional[str] = None

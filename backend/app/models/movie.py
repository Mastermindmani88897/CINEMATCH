from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    Float, JSON, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True, nullable=True)
    title = Column(String(500), nullable=False, index=True)
    original_title = Column(String(500), nullable=True)
    overview = Column(Text, nullable=True)
    tagline = Column(Text, nullable=True)
    genres = Column(JSON, nullable=True)           # ["Action", "Drama"]
    keywords = Column(JSON, nullable=True)          # ["space", "time travel"]
    cast = Column(JSON, nullable=True)              # [{"name": "...", "character": "..."}]
    crew = Column(JSON, nullable=True)              # [{"name": "...", "job": "Director"}]
    director = Column(String(255), nullable=True)
    production_companies = Column(JSON, nullable=True)
    runtime = Column(Integer, nullable=True)        # minutes
    release_date = Column(String(20), nullable=True)
    release_year = Column(Integer, nullable=True, index=True)
    vote_average = Column(Float, default=0.0, index=True)
    vote_count = Column(Integer, default=0)
    popularity = Column(Float, default=0.0, index=True)
    original_language = Column(String(10), nullable=True)
    budget = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    poster_path = Column(Text, nullable=True)
    backdrop_path = Column(Text, nullable=True)
    trailer_key = Column(String(50), nullable=True)  # YouTube video ID
    imdb_id = Column(String(20), nullable=True)
    status = Column(String(50), nullable=True)       # Released, Post Production, etc.
    adult = Column(Boolean, default=False)
    weighted_rating = Column(Float, default=0.0, index=True)
    trending_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    favorites = relationship("Favorite", back_populates="movie", cascade="all, delete-orphan")
    watchlist_items = relationship("Watchlist", back_populates="movie", cascade="all, delete-orphan")
    watch_history = relationship("WatchHistory", back_populates="movie", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="movie", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="movie", cascade="all, delete-orphan")
    notes = relationship("MovieNote", back_populates="movie", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_movies_weighted_rating", "weighted_rating"),
        Index("idx_movies_popularity", "popularity"),
        Index("idx_movies_release_year", "release_year"),
    )


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="favorites")
    movie = relationship("Movie", back_populates="favorites")


class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="watchlist")
    movie = relationship("Movie", back_populates="watchlist_items")


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    watched_at = Column(DateTime(timezone=True), server_default=func.now())
    progress = Column(Float, default=0.0)  # 0.0 - 1.0

    user = relationship("User", back_populates="watch_history")
    movie = relationship("Movie", back_populates="watch_history")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Float, nullable=False)  # 0.5 - 5.0
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    likes = Column(Integer, default=0)
    contains_spoilers = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="reviews")
    movie = relationship("Movie", back_populates="reviews")


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    query = Column(String(500), nullable=False)
    result_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="search_history")


class MovieNote(Base):
    __tablename__ = "movie_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="notes")
    movie = relationship("Movie", back_populates="notes")


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="SET NULL"), nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

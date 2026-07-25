from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache
from typing import Optional, List


class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "CineMatch AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # MongoDB Atlas Configuration
    MONGODB_URI: str = ""
    DATABASE_NAME: str = "cinematch_db"

    # JWT Security Configuration
    JWT_SECRET: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # TMDB API Configuration
    TMDB_API_KEY: str = ""
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p"

    # Google Gemini AI API Configuration
    GEMINI_API_KEY: str = ""

    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_NAME: str = "CineMatch AI"
    EMAILS_FROM_EMAIL: str = "noreply@cinematch.ai"

    # Frontend Integration & CORS
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,https://cinematch-web.vercel.app"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Machine Learning Directories
    ML_MODELS_DIR: str = "./ml/models"
    ML_DATA_DIR: str = "./ml/data"

    # Redis Cache Configuration
    REDIS_URL: Optional[str] = None

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

"""
CineMatch AI — Recommendation System API Router
Provides independent, non-leaking recommendation endpoints for Industry, Mood, Genre, Popularity, and Semantic AI Search.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import random
import logging
from datetime import datetime, timezone

from app.core.database import get_database
from app.core.utils import serialize_doc
from app.schemas.recommendation import (
    RecommendationResponse, RecommendationItem,
    SemanticSearchRequest
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Explicit Industry → Language/Filter mapping
INDUSTRY_MAP = {
    "tollywood": {"original_language": "te"},
    "bollywood": {"original_language": "hi"},
    "kollywood": {"original_language": "ta"},
    "mollywood": {"original_language": "ml"},
    "sandalwood": {"original_language": "kn"},
    "hollywood": {"original_language": "en"},
    "korean": {"original_language": "ko"},
    "japanese": {"original_language": "ja"},
    "chinese": {"original_language": {"$in": ["zh", "cn"]}},
    "anime": {"genres": "Animation", "original_language": "ja"},
    "international": {"original_language": {"$ne": "en"}},
}

# Explicit Mood → Genre & Keyword mapping
MOOD_CONFIG = {
    "happy": {
        "include_genres": ["Comedy", "Animation", "Family", "Music"],
        "exclude_genres": ["Horror", "War", "Crime"],
        "keywords": ["funny", "laugh", "cheerful", "uplifting", "fun", "hilarious", "lighthearted", "heartwarming"],
        "explanation": "Uplifting, funny, and joyful films to boost your mood!"
    },
    "sad": {
        "include_genres": ["Drama", "Romance"],
        "exclude_genres": ["Action", "Comedy", "Animation"],
        "keywords": ["tearjerker", "tragic", "loss", "grief", "heartbreak", "emotional", "sorrow", "melancholy"],
        "explanation": "Deeply moving emotional dramas for a reflective mood."
    },
    "romantic": {
        "include_genres": ["Romance"],
        "exclude_genres": ["Horror", "War", "Action"],
        "keywords": ["love", "romance", "relationship", "couple", "passion", "wedding", "affair", "crush", "lover"],
        "explanation": "Heartfelt romantic tales and love stories."
    },
    "action": {
        "include_genres": ["Action", "Adventure"],
        "exclude_genres": ["Documentary", "Romance"],
        "keywords": ["fight", "explosion", "martial arts", "battle", "spy", "agent", "chase", "superhero", "rescue"],
        "explanation": "High-octane action and adrenaline-fueled adventures."
    },
    "motivational": {
        "include_genres": ["Drama", "History", "Biography"],
        "exclude_genres": ["Horror"],
        "keywords": ["inspirational", "heroic", "triumph", "dream", "success", "overcome", "courage", "determination", "championship", "true story"],
        "explanation": "Inspiring stories of perseverance, courage, and triumph."
    },
    "thriller": {
        "include_genres": ["Thriller", "Mystery", "Crime"],
        "exclude_genres": ["Animation", "Family"],
        "keywords": ["suspense", "serial killer", "investigation", "twist", "murder", "conspiracy", "psychological", "kidnapping"],
        "explanation": "Edge-of-your-seat suspense and gripping mystery thrillers."
    },
    "dark": {
        "include_genres": ["Crime", "Horror", "Thriller", "Drama"],
        "exclude_genres": ["Family", "Animation"],
        "keywords": ["gritty", "dark", "dystopian", "sinister", "macabre", "vengeance", "morally grey", "noir", "psychological"],
        "explanation": "Intense, gritty, and dark cinematic experiences."
    },
    "comedy": {
        "include_genres": ["Comedy"],
        "exclude_genres": ["Horror", "War"],
        "keywords": ["hilarious", "parody", "satire", "sitcom", "goofy", "prank", "jokes", "fool", "humor"],
        "explanation": "Hilarious comedies and laugh-out-loud entertainment."
    },
    "family": {
        "include_genres": ["Family", "Animation"],
        "exclude_genres": ["Horror", "Crime", "War"],
        "keywords": ["kids", "family", "children", "pet", "magic", "adventure", "toy", "friendly", "cartoon"],
        "explanation": "Wholesome entertainment for all ages to enjoy together."
    },
    "adventure": {
        "include_genres": ["Adventure", "Fantasy"],
        "exclude_genres": ["Romance"],
        "keywords": ["expedition", "treasure", "quest", "journey", "island", "jungle", "exploration", "space", "magic"],
        "explanation": "Epic journeys and fantasy adventure quests."
    },
    "crime": {
        "include_genres": ["Crime", "Mystery"],
        "exclude_genres": ["Family", "Animation"],
        "keywords": ["mafia", "robbery", "gangster", "police", "detective", "heist", "smuggling", "underworld"],
        "explanation": "Gritty crime sagas, police procedurals, and heist thrillers."
    },
    "horror": {
        "include_genres": ["Horror"],
        "exclude_genres": ["Comedy", "Family"],
        "keywords": ["ghost", "possession", "demon", "monster", "zombie", "haunted", "blood", "slasher", "nightmare"],
        "explanation": "Spooky, chilling, and terrifying horror films."
    },
    "scifi": {
        "include_genres": ["Science Fiction"],
        "exclude_genres": ["Romance", "Music"],
        "keywords": ["space", "alien", "robot", "time travel", "future", "ai", "cyborg", "galaxy", "technology"],
        "explanation": "Mind-bending futuristic sci-fi and cosmic explorations."
    }
}


def format_recs(recs: list, algorithm: str, total: Optional[int] = None, page: int = 1, pages: int = 1) -> RecommendationResponse:
    items = []
    seen = set()
    for r in recs:
        mid = r["movie_id"]
        if mid in seen:
            continue
        seen.add(mid)
        items.append(
            RecommendationItem(
                movie_id=mid,
                title=r["title"],
                poster_path=r.get("poster_path"),
                vote_average=r.get("vote_average", 0),
                release_year=r.get("release_year"),
                genres=r.get("genres", []),
                similarity_score=r.get("similarity_score", 0.90),
                match_percentage=r.get("match_percentage", 90),
                explanation=r.get("explanation"),
            )
        )
    tot = total if total is not None else len(items)
    return RecommendationResponse(recommendations=items, algorithm=algorithm, total=tot, page=page, pages=pages)


def interleave_by_industry(candidates: list, max_per_lang_ratio: float = 0.35, target_limit: int = 100) -> list:
    """
    Re-ranks candidates to eliminate Hollywood / single-language bias.
    Interleaves candidates from different original languages so recommendations contain global diversity.
    """
    if not candidates:
        return []

    # Group candidates by original_language
    lang_groups = {}
    for m in candidates:
        lang = str(m.get("original_language", "en")).lower()
        if lang not in lang_groups:
            lang_groups[lang] = []
        lang_groups[lang].append(m)

    result = []
    seen_ids = set()
    max_single_lang = max(1, int(target_limit * max_per_lang_ratio))
    lang_counts = {lang: 0 for lang in lang_groups}

    active_langs = list(lang_groups.keys())

    # First pass: Interleave while adhering to max_single_lang constraint
    while active_langs and len(result) < target_limit:
        next_active = []
        for lang in active_langs:
            group = lang_groups[lang]
            if group and lang_counts[lang] < max_single_lang:
                m = group.pop(0)
                mid = m.get("id", m.get("tmdb_id"))
                if mid not in seen_ids:
                    seen_ids.add(mid)
                    result.append(m)
                    lang_counts[lang] += 1
            if group and lang_counts[lang] < max_single_lang:
                next_active.append(lang)
        if len(next_active) == len(active_langs):
            break
        active_langs = next_active

    # Second pass: Fill remaining slots if any left
    if len(result) < target_limit:
        for m in candidates:
            mid = m.get("id", m.get("tmdb_id"))
            if mid not in seen_ids:
                seen_ids.add(mid)
                result.append(m)
            if len(result) >= target_limit:
                break

    return result


from ml.pipeline.explanation_engine import ExplanationGenerator
explainer = ExplanationGenerator()


# ── 1. Industry / Regional Recommendations ──────────────────────────────────
@router.get("/industry/{industry}", response_model=RecommendationResponse)
async def industry_based(
    industry: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    limit: Optional[int] = Query(None, ge=1, le=1000),
):
    ind_lower = industry.lower().strip()
    db = get_database()
    recs = []

    query = INDUSTRY_MAP.get(ind_lower, {"original_language": ind_lower[:2]})
    total_count = await db.movies.count_documents(query)

    effective_per_page = limit if limit else per_page
    skip_val = (page - 1) * effective_per_page

    cursor = db.movies.find(query).sort("popularity", -1).skip(skip_val).limit(effective_per_page)
    candidates = [m async for m in cursor]

    if not candidates and page == 1:
        cursor = db.movies.find(query).limit(effective_per_page)
        candidates = [m async for m in cursor]

    if candidates:
        for m in candidates:
            m_dict = {
                "title": m.get("title", ""),
                "genres": m.get("genres", []),
                "vote_average": m.get("vote_average", 0),
            }
            exp_text = explainer.generate_industry_explanation(ind_lower, m_dict)
            recs.append({
                "movie_id": m.get("id", m.get("tmdb_id")),
                "title": m.get("title", ""),
                "poster_path": m.get("poster_path", ""),
                "vote_average": m.get("vote_average", 0),
                "release_year": m.get("release_year", 2024),
                "genres": m.get("genres", []),
                "similarity_score": 0.95,
                "match_percentage": 95,
                "explanation": exp_text,
            })

    total_pages = max(1, (total_count + effective_per_page - 1) // effective_per_page)
    return format_recs(recs, f"industry-{ind_lower}", total=total_count, page=page, pages=total_pages)


# ── 2. Mood-Based Recommendations (Global Multi-Industry) ────────────────────
@router.get("/mood/{mood}", response_model=RecommendationResponse)
async def mood_based(
    mood: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    limit: Optional[int] = Query(None, ge=1, le=1000),
):
    mood_key = mood.lower().replace("-", "").replace(" ", "")
    db = get_database()
    recs = []

    config = MOOD_CONFIG.get(mood_key, {
        "include_genres": ["Drama"],
        "exclude_genres": [],
        "keywords": [],
        "explanation": f"Recommended films matching {mood.capitalize()} mood"
    })

    query = {
        "genres": {"$in": config["include_genres"]}
    }
    if config.get("exclude_genres"):
        query["genres"]["$nin"] = config["exclude_genres"]

    total_count = await db.movies.count_documents(query)
    effective_per_page = limit if limit else per_page
    skip_val = (page - 1) * effective_per_page

    cursor = db.movies.find(query).sort("vote_average", -1).skip(skip_val).limit(effective_per_page)
    candidates = [m async for m in cursor]

    if not candidates and page == 1:
        cursor = db.movies.find({"genres": {"$in": config["include_genres"]}}).sort("vote_average", -1).limit(effective_per_page)
        candidates = [m async for m in cursor]

    scored = []
    keywords = config.get("keywords", [])
    for m in candidates:
        score = float(m.get("weighted_rating", m.get("vote_average", 7.0)))
        text = f"{m.get('title', '')} {m.get('overview', '')} {m.get('tagline', '')}".lower()
        keyword_matches = sum(1 for kw in keywords if kw in text)
        score += (keyword_matches * 1.5)
        scored.append((score, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    all_sorted = [m for _, m in scored]

    top_candidates = interleave_by_industry(all_sorted, max_per_lang_ratio=0.35, target_limit=effective_per_page)

    for m in top_candidates:
        m_dict = {
            "title": m.get("title", ""),
            "genres": m.get("genres", []),
            "vote_average": m.get("vote_average", 0),
        }
        exp_text = explainer.generate_mood_explanation(mood, m_dict)
        recs.append({
            "movie_id": m.get("id", m.get("tmdb_id")),
            "title": m.get("title", ""),
            "poster_path": m.get("poster_path", ""),
            "vote_average": m.get("vote_average", 0),
            "release_year": m.get("release_year", 2024),
            "genres": m.get("genres", []),
            "similarity_score": 0.92,
            "match_percentage": 92,
            "explanation": exp_text,
        })

    total_pages = max(1, (total_count + effective_per_page - 1) // effective_per_page)
    return format_recs(recs, f"mood-{mood_key}", total=total_count, page=page, pages=total_pages)


# ── 3. Genre-Based Recommendations (Global Multi-Industry) ───────────────────
@router.get("/genre", response_model=RecommendationResponse)
async def genre_based(
    genres: str = Query(..., description="Comma-separated genres"),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    limit: Optional[int] = Query(None, ge=1, le=1000),
):
    genre_list = [g.strip() for g in genres.split(",") if g.strip()]
    recs = []
    db = get_database()

    query = {"genres": {"$all": genre_list}} if len(genre_list) > 1 else {"genres": {"$in": genre_list}}
    total_count = await db.movies.count_documents(query)

    effective_per_page = limit if limit else per_page
    skip_val = (page - 1) * effective_per_page

    cursor = db.movies.find(query).sort("vote_average", -1).skip(skip_val).limit(effective_per_page)
    candidates = [m async for m in cursor]

    if not candidates and len(genre_list) > 1 and page == 1:
        query = {"genres": {"$in": genre_list}}
        total_count = await db.movies.count_documents(query)
        cursor = db.movies.find(query).sort("vote_average", -1).limit(effective_per_page)
        candidates = [m async for m in cursor]

    top_candidates = interleave_by_industry(candidates, max_per_lang_ratio=0.35, target_limit=effective_per_page)

    for m in top_candidates:
        m_dict = {
            "title": m.get("title", ""),
            "genres": m.get("genres", []),
            "vote_average": m.get("vote_average", 0),
        }
        exp_text = explainer.generate_genre_explanation(genres, m_dict)
        recs.append({
            "movie_id": m.get("id", m.get("tmdb_id")),
            "title": m.get("title", ""),
            "poster_path": m.get("poster_path", ""),
            "vote_average": m.get("vote_average", 0),
            "release_year": m.get("release_year", 2024),
            "genres": m.get("genres", []),
            "similarity_score": 0.88,
            "match_percentage": 88,
            "explanation": exp_text,
        })

    total_pages = max(1, (total_count + effective_per_page - 1) // effective_per_page)
    return format_recs(recs, "genre-based", total=total_count, page=page, pages=total_pages)


# ── 4. Popularity-Based Recommendations (Global Multi-Industry) ──────────────
@router.get("/popular", response_model=RecommendationResponse)
async def popularity_based(
    mode: str = Query("weighted", pattern="^(weighted|trending|popular|top_rated)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    limit: Optional[int] = Query(None, ge=1, le=1000),
):
    db = get_database()
    recs = []
    sort_field = "trending_score" if mode == "trending" else ("popularity" if mode == "popular" else "weighted_rating")

    total_count = await db.movies.count_documents({})
    effective_per_page = limit if limit else per_page
    skip_val = (page - 1) * effective_per_page

    cursor = db.movies.find({}).sort(sort_field, -1).skip(skip_val).limit(effective_per_page)
    candidates = [m async for m in cursor]
    top_candidates = interleave_by_industry(candidates, max_per_lang_ratio=0.35, target_limit=effective_per_page)

    for m in top_candidates:
        m_dict = {
            "title": m.get("title", ""),
            "genres": m.get("genres", []),
            "vote_average": m.get("vote_average", 0),
        }
        exp_text = explainer.generate_popularity_explanation(mode, m_dict)
        recs.append({
            "movie_id": m.get("id", m.get("tmdb_id")),
            "title": m.get("title", ""),
            "poster_path": m.get("poster_path", ""),
            "vote_average": m.get("vote_average", 0),
            "release_year": m.get("release_year", 2024),
            "genres": m.get("genres", []),
            "similarity_score": 0.90,
            "match_percentage": 90,
            "explanation": exp_text,
        })

    total_pages = max(1, (total_count + effective_per_page - 1) // effective_per_page)
    return format_recs(recs, f"popular-{mode}", total=total_count, page=page, pages=total_pages)


# ── 5. Semantic Search Recommendations (Global Multi-Industry) ───────────────
@router.post("/semantic", response_model=RecommendationResponse)
async def semantic_search(request: SemanticSearchRequest):
    recs = []
    db = get_database()
    q_clean = request.query.strip()

    cursor = db.movies.find({
        "$or": [
            {"title": {"$regex": q_clean, "$options": "i"}},
            {"overview": {"$regex": q_clean, "$options": "i"}},
            {"genres": {"$regex": q_clean, "$options": "i"}},
            {"keywords": {"$regex": q_clean, "$options": "i"}},
            {"tagline": {"$regex": q_clean, "$options": "i"}},
        ]
    }).sort("vote_average", -1).limit(200)

    candidates = [m async for m in cursor]
    top_candidates = interleave_by_industry(candidates, max_per_lang_ratio=0.35, target_limit=request.limit)

    for m in top_candidates:
        recs.append({
            "movie_id": m.get("id", m.get("tmdb_id")),
            "title": m.get("title", ""),
            "poster_path": m.get("poster_path", ""),
            "vote_average": m.get("vote_average", 0),
            "release_year": m.get("release_year", 2024),
            "genres": m.get("genres", []),
            "similarity_score": 0.89,
            "match_percentage": 89,
            "explanation": f"Handpicked match based on your query: '{q_clean}'",
        })

    return format_recs(recs, "semantic-search")


# ── 6. Metadata Endpoints ──────────────────────────────────────────────────
@router.get("/moods")
async def get_moods():
    return {"moods": list(MOOD_CONFIG.keys())}


@router.get("/industries")
async def get_industries():
    return {"industries": list(INDUSTRY_MAP.keys())}

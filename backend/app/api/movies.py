"""
Movie routes: list, detail, trending, popular, top-rated, upcoming, genres using MongoDB Atlas with live TMDB API fallbacks.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from app.core.database import get_database
from app.core.utils import serialize_doc
from app.schemas.movie import MovieResponse, MovieListResponse, PaginatedMovies
from app.services import tmdb_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/movies", tags=["Movies"])

TMDB_GENRES_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}

INDUSTRY_LANG_MAP = {
    "tollywood": "te",
    "bollywood": "hi",
    "kollywood": "ta",
    "mollywood": "ml",
    "sandalwood": "kn",
    "korean": "ko",
    "japanese": "ja",
    "anime": "ja",
    "chinese": "zh",
    "hollywood": "en",
    "telugu": "te",
    "hindi": "hi",
    "tamil": "ta",
    "malayalam": "ml",
    "kannada": "kn",
    "english": "en",
}


def map_tmdb_to_list_response(item: dict) -> dict:
    tmdb_id = item.get("id") or 1
    title = item.get("title") or item.get("name") or "Untitled"
    release_date = item.get("release_date") or item.get("first_air_date") or ""
    release_year = int(release_date[:4]) if len(release_date) >= 4 and release_date[:4].isdigit() else 2024

    genres = []
    if "genres" in item and isinstance(item["genres"], list):
        genres = [g.get("name") if isinstance(g, dict) else str(g) for g in item["genres"]]
    elif "genre_ids" in item and isinstance(item["genre_ids"], list):
        genres = [TMDB_GENRES_MAP.get(gid, "Drama") for gid in item["genre_ids"]]

    vote_avg = float(item.get("vote_average") or 0.0)

    return {
        "id": int(tmdb_id),
        "tmdb_id": int(tmdb_id),
        "title": str(title),
        "overview": str(item.get("overview") or ""),
        "genres": genres,
        "release_year": release_year,
        "vote_average": vote_avg,
        "popularity": float(item.get("popularity") or 0.0),
        "weighted_rating": round(vote_avg, 2),
        "poster_path": item.get("poster_path"),
        "backdrop_path": item.get("backdrop_path"),
        "runtime": int(item.get("runtime") or 120),
        "original_language": str(item.get("original_language") or "en"),
    }


def compute_financials(budget: float, revenue: float) -> dict:
    if not budget or budget <= 0:
        return {
            "profit_loss": None,
            "roi_percentage": None,
            "recovery_percentage": None,
            "collection_multiplier": None,
            "box_office_status": None
        }

    profit = revenue - budget
    roi = (profit / budget) * 100
    recovery = (revenue / budget) * 100
    multiplier = round(revenue / budget, 2)

    if revenue >= 2.5 * budget:
        status = "Blockbuster"
    elif revenue >= 1.5 * budget:
        status = "Super Hit"
    elif revenue >= budget:
        status = "Profitable / Hit"
    elif revenue >= 0.8 * budget:
        status = "Average / Break Even"
    else:
        status = "Box Office Failure"

    return {
        "profit_loss": round(profit, 2),
        "roi_percentage": round(roi, 1),
        "recovery_percentage": round(recovery, 1),
        "collection_multiplier": multiplier,
        "box_office_status": status
    }


def map_tmdb_to_detail_response(item: dict) -> dict:
    base = map_tmdb_to_list_response(item)

    credits = item.get("credits") or {}
    raw_cast = credits.get("cast") or item.get("cast") or []
    raw_crew = credits.get("crew") or item.get("crew") or []

    cast_list = []
    for c in raw_cast[:20]:
        if isinstance(c, dict):
            cast_list.append({
                "name": c.get("name", ""),
                "character": c.get("character", ""),
                "profile_path": c.get("profile_path"),
                "order": c.get("order", 0)
            })

    crew_list = []
    directors = []
    writers = []
    screenplay = []
    story = []
    producers = []
    exec_producers = []
    music = []
    editors = []
    cinematography = []

    for cr in raw_crew:
        if isinstance(cr, dict):
            name = cr.get("name", "")
            job = cr.get("job", "")
            dept = cr.get("department", "")
            crew_list.append({
                "name": name,
                "job": job,
                "department": dept,
                "profile_path": cr.get("profile_path")
            })
            if job == "Director" and name not in directors:
                directors.append(name)
            if (job in ("Writer", "Screenplay", "Story") or dept == "Writing") and name not in writers:
                writers.append(name)
            if job == "Screenplay" and name not in screenplay:
                screenplay.append(name)
            if job == "Story" and name not in story:
                story.append(name)
            if job == "Producer" and name not in producers:
                producers.append(name)
            if job == "Executive Producer" and name not in exec_producers:
                exec_producers.append(name)
            if job in ("Original Music Composer", "Music") and name not in music:
                music.append(name)
            if job == "Editor" and name not in editors:
                editors.append(name)
            if job in ("Director of Photography", "Cinematography") and name not in cinematography:
                cinematography.append(name)

    kw_raw = item.get("keywords")
    keywords = []
    if isinstance(kw_raw, dict):
        kw_items = kw_raw.get("keywords") or kw_raw.get("results") or []
        keywords = [k.get("name") for k in kw_items if isinstance(k, dict)]
    elif isinstance(kw_raw, list):
        keywords = [k.get("name") if isinstance(k, dict) else str(k) for k in kw_raw]

    videos_raw = item.get("videos")
    trailer_key = item.get("trailer_key")
    if not trailer_key and isinstance(videos_raw, dict):
        v_results = videos_raw.get("results", [])
        for v in v_results:
            if v.get("site") == "YouTube" and v.get("type") in ("Trailer", "Teaser"):
                trailer_key = v.get("key")
                break

    spoken_languages = [
        l.get("english_name", l.get("name"))
        for l in item.get("spoken_languages", [])
        if isinstance(l, dict)
    ]

    budget = float(item.get("budget") or 0)
    revenue = float(item.get("revenue") or 0)
    fin = compute_financials(budget, revenue)

    base.update({
        "tagline": str(item.get("tagline") or ""),
        "keywords": keywords,
        "cast": cast_list,
        "crew": crew_list[:50],
        "director": ", ".join(directors) if directors else (item.get("director") or ""),
        "writers": writers,
        "screenplay": screenplay,
        "story": story,
        "producers": producers,
        "executive_producers": exec_producers,
        "music_composers": music,
        "editors": editors,
        "cinematographers": cinematography,
        "production_companies": [p.get("name") for p in item.get("production_companies", [])] if isinstance(item.get("production_companies"), list) else [],
        "distributors": item.get("distributors") or [],
        "spoken_languages": spoken_languages,
        "collection": item.get("belongs_to_collection"),
        "homepage": item.get("homepage"),
        "status": item.get("status"),
        "certification": item.get("certification"),
        "streaming_providers": ["Netflix", "Amazon Prime Video", "Disney+"],
        "trailer_key": trailer_key,
        "imdb_id": item.get("imdb_id"),
        "budget": budget,
        "revenue": revenue,
        "profit_loss": fin["profit_loss"],
        "roi_percentage": fin["roi_percentage"],
        "recovery_percentage": fin["recovery_percentage"],
        "collection_multiplier": fin["collection_multiplier"],
        "box_office_status": fin["box_office_status"],
        "watch_providers": item.get("watch_providers"),
        "trending_score": float(item.get("popularity") or 0.0),
        "created_at": datetime.now(),
    })
    return base


@router.get("", response_model=PaginatedMovies)
@router.get("/", response_model=PaginatedMovies)
@router.get("/discover", response_model=PaginatedMovies)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    genre: Optional[str] = None,
    genres: Optional[str] = None,
    industry: Optional[str] = None,
    year: Optional[int] = None,
    language: Optional[str] = None,
    country: Optional[str] = None,
    min_rating: float = Query(0, ge=0, le=10),
    sort: str = Query("popularity", pattern="^(popularity|vote_average|release_year|weighted_rating)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    try:
        db = get_database()
        query = {}

        # Handle Industry / Language aliasing
        target_ind = (industry or language or "").lower().strip()
        if target_ind in INDUSTRY_LANG_MAP:
            query["original_language"] = INDUSTRY_LANG_MAP[target_ind]
            if target_ind == "anime":
                query["genres"] = "Animation"

        # Handle Multi-Select Genres (e.g., "Action,Adventure")
        genres_input = genre or genres
        if genres_input:
            g_list = [g.strip() for g in genres_input.split(",") if g.strip()]
            real_genres = []
            for g in g_list:
                if g.lower() in INDUSTRY_LANG_MAP and "original_language" not in query:
                    query["original_language"] = INDUSTRY_LANG_MAP[g.lower()]
                    if g.lower() == "anime":
                        real_genres.append("Animation")
                elif g.lower() not in INDUSTRY_LANG_MAP:
                    real_genres.append(g)

            if len(real_genres) > 1:
                query["genres"] = {"$all": real_genres}
            elif len(real_genres) == 1:
                query["genres"] = real_genres[0]

        if year:
            query["release_year"] = year
        if language and language.lower().strip() in INDUSTRY_LANG_MAP and "original_language" not in query:
            query["original_language"] = INDUSTRY_LANG_MAP[language.lower().strip()]
        elif language and "original_language" not in query:
            query["original_language"] = language
        if country:
            query["origin_country"] = country
        if min_rating > 0:
            query["vote_average"] = {"$gte": min_rating}

        sort_order = -1 if order == "desc" else 1

        total = await db.movies.count_documents(query)
        if total > 0:
            cursor = (
                db.movies.find(query)
                .sort(sort, sort_order)
                .skip((page - 1) * per_page)
                .limit(per_page)
            )
            movies = [serialize_doc(m) async for m in cursor]
            return PaginatedMovies(
                items=[MovieListResponse.model_validate(m) for m in movies],
                total=total,
                page=page,
                per_page=per_page,
                pages=(total + per_page - 1) // per_page,
            )
    except Exception as e:
        logger.warning(f"MongoDB query failed in list_movies ({e}). Falling back to TMDB API...")

    # TMDB Fallback
    try:
        tmdb_data = await tmdb_service.get_popular_movies(page=page)
        results = tmdb_data.get("results", [])
        items = [MovieListResponse.model_validate(map_tmdb_to_list_response(item)) for item in results[:per_page]]
        total_results = tmdb_data.get("total_results", len(items))

        return PaginatedMovies(
            items=items,
            total=total_results,
            page=page,
            per_page=per_page,
            pages=tmdb_data.get("total_pages", 1),
        )
    except Exception as exc:
        logger.warning(f"TMDB fallback failed in list_movies: {exc}")
        return PaginatedMovies(
            items=[],
            total=0,
            page=page,
            per_page=per_page,
            pages=0,
        )


@router.get("/trending", response_model=List[MovieListResponse])
async def get_trending(limit: int = Query(20, le=50)):
    try:
        db = get_database()
        cursor = db.movies.find({}).sort("trending_score", -1).limit(limit)
        movies = [serialize_doc(m) async for m in cursor]
        if movies:
            return [MovieListResponse.model_validate(m) for m in movies]
    except Exception as e:
        logger.warning(f"MongoDB query failed in get_trending ({e}). Falling back to TMDB API...")

    tmdb_data = await tmdb_service.get_trending_movies(time_window="day", page=1)
    results = tmdb_data.get("results", [])
    return [MovieListResponse.model_validate(map_tmdb_to_list_response(m)) for m in results[:limit]]


@router.get("/popular", response_model=List[MovieListResponse])
async def get_popular(limit: int = Query(20, le=50)):
    try:
        db = get_database()
        cursor = db.movies.find({}).sort("popularity", -1).limit(limit)
        movies = [serialize_doc(m) async for m in cursor]
        if movies:
            return [MovieListResponse.model_validate(m) for m in movies]
    except Exception as e:
        logger.warning(f"MongoDB query failed in get_popular ({e}). Falling back to TMDB API...")

    tmdb_data = await tmdb_service.get_popular_movies(page=1)
    results = tmdb_data.get("results", [])
    return [MovieListResponse.model_validate(map_tmdb_to_list_response(m)) for m in results[:limit]]


@router.get("/top-rated", response_model=List[MovieListResponse])
async def get_top_rated(
    limit: int = Query(20, le=50),
    min_votes: int = Query(100, ge=0),
):
    try:
        db = get_database()
        cursor = (
            db.movies.find({"vote_count": {"$gte": min_votes}})
            .sort("weighted_rating", -1)
            .limit(limit)
        )
        movies = [serialize_doc(m) async for m in cursor]
        if movies:
            return [MovieListResponse.model_validate(m) for m in movies]
    except Exception as e:
        logger.warning(f"MongoDB query failed in get_top_rated ({e}). Falling back to TMDB API...")

    tmdb_data = await tmdb_service.get_top_rated_movies(page=1)
    results = tmdb_data.get("results", [])
    return [MovieListResponse.model_validate(map_tmdb_to_list_response(m)) for m in results[:limit]]


@router.get("/top-rated-catalog", response_model=PaginatedMovies)
async def top_rated_catalog(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    industry: Optional[str] = None,
    language: Optional[str] = None,
    year: Optional[int] = None,
    genre: Optional[str] = None,
    country: Optional[str] = None,
    preset: Optional[str] = Query("all_time", pattern="^(top_100|top_250|top_500|top_1000|all_time)$"),
    min_rating: float = Query(0, ge=0, le=10),
    min_votes: int = Query(10, ge=0),
):
    db = get_database()
    query = {"vote_count": {"$gte": min_votes}}

    target_ind = (industry or language or "").lower().strip()
    if target_ind in INDUSTRY_LANG_MAP:
        query["original_language"] = INDUSTRY_LANG_MAP[target_ind]
    elif language and language.lower().strip() in INDUSTRY_LANG_MAP:
        query["original_language"] = INDUSTRY_LANG_MAP[language.lower().strip()]
    elif language:
        query["original_language"] = language

    if year:
        query["release_year"] = year
    if genre:
        query["genres"] = genre
    if country:
        query["origin_country"] = country
    if min_rating > 0:
        query["vote_average"] = {"$gte": min_rating}

    limit_cap = 100000
    if preset == "top_100":
        limit_cap = 100
    elif preset == "top_250":
        limit_cap = 250
    elif preset == "top_500":
        limit_cap = 500
    elif preset == "top_1000":
        limit_cap = 1000

    total_matched = await db.movies.count_documents(query)
    effective_total = min(total_matched, limit_cap)

    cursor = (
        db.movies.find(query)
        .sort("weighted_rating", -1)
        .skip((page - 1) * per_page)
        .limit(min(per_page, max(0, effective_total - (page - 1) * per_page)))
    )
    movies = [serialize_doc(m) async for m in cursor]

    return PaginatedMovies(
        items=[MovieListResponse.model_validate(m) for m in movies],
        total=effective_total,
        page=page,
        per_page=per_page,
        pages=max(1, (effective_total + per_page - 1) // per_page),
    )


@router.get("/{movie_id}/watch-providers")
async def get_watch_providers(movie_id: int):
    try:
        data = await tmdb_service.get_movie_watch_providers(movie_id)
        return data.get("results", {})
    except Exception as e:
        logger.warning(f"Failed to fetch watch providers for {movie_id}: {e}")
        return {}


@router.get("/genres", response_model=List[str])
async def get_genres():
    try:
        db = get_database()
        genres = await db.movies.distinct("genres")
        if genres:
            return sorted([g for g in genres if g and isinstance(g, str)])
    except Exception:
        pass
    return sorted(list(set(TMDB_GENRES_MAP.values())))


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int):
    db = get_database()
    movie = await db.movies.find_one({"id": movie_id})

    if not movie:
        movie = await db.movies.find_one({"tmdb_id": movie_id})

    # Auto-enrich missing cast/crew/director from TMDB API
    if movie and (not movie.get("cast") or not movie.get("director") or not movie.get("writers")):
        try:
            tmdb_id = movie.get("tmdb_id") or movie.get("id")
            tmdb_data = await tmdb_service.get_movie_details(tmdb_id)
            if tmdb_data and "id" in tmdb_data:
                enriched = map_tmdb_to_detail_response(tmdb_data)
                update_fields = {
                    "cast": enriched.get("cast", []),
                    "crew": enriched.get("crew", []),
                    "director": enriched.get("director", ""),
                    "writers": enriched.get("writers", []),
                    "screenplay": enriched.get("screenplay", []),
                    "story": enriched.get("story", []),
                    "producers": enriched.get("producers", []),
                    "executive_producers": enriched.get("executive_producers", []),
                    "music_composers": enriched.get("music_composers", []),
                    "editors": enriched.get("editors", []),
                    "cinematographers": enriched.get("cinematographers", []),
                    "production_companies": enriched.get("production_companies", []),
                    "spoken_languages": enriched.get("spoken_languages", []),
                    "keywords": enriched.get("keywords", []),
                    "budget": enriched.get("budget", 0),
                    "revenue": enriched.get("revenue", 0),
                    "tagline": enriched.get("tagline", ""),
                    "homepage": enriched.get("homepage"),
                    "status": enriched.get("status"),
                }
                if enriched.get("trailer_key"):
                    update_fields["trailer_key"] = enriched["trailer_key"]

                await db.movies.update_one({"_id": movie["_id"]}, {"$set": update_fields})
                movie.update(update_fields)
        except Exception as e:
            logger.warning(f"Could not live-enrich movie {movie_id} from TMDB: {e}")

    if movie:
        doc = serialize_doc(movie)
        # Compute financial metrics on-the-fly from stored budget/revenue
        budget_val = float(doc.get("budget") or 0)
        revenue_val = float(doc.get("revenue") or 0)
        fin = compute_financials(budget_val, revenue_val)
        doc.update(fin)
        return MovieResponse.model_validate(doc)

    try:
        tmdb_data = await tmdb_service.get_movie_details(movie_id)
        if tmdb_data and "id" in tmdb_data:
            detail = map_tmdb_to_detail_response(tmdb_data)
            return MovieResponse.model_validate(detail)
    except Exception as e:
        logger.warning(f"TMDB detail lookup failed for {movie_id}: {e}")

    raise HTTPException(status_code=404, detail="Movie not found")

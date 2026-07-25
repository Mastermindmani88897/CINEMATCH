"""Admin routes: user management, movie CRUD, ML retraining using MongoDB Atlas."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from datetime import datetime, timezone

from app.core.database import get_database
from app.core.deps import get_current_admin
from app.core.utils import serialize_doc
from app.schemas.movie import MovieCreate, MovieUpdate, MovieResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── User Management ───────────────────────────────────────────────────────────
@router.get("/users")
async def list_users(
    page: int = 1,
    per_page: int = 20,
    admin: dict = Depends(get_current_admin),
):
    db = get_database()
    total = await db.users.count_documents({})
    cursor = db.users.find({}).sort("id", 1).skip((page - 1) * per_page).limit(per_page)
    users = [serialize_doc(u) async for u in cursor]
    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1,
    }


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    admin: dict = Depends(get_current_admin),
):
    db = get_database()
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(404, "User not found")
    if user["id"] == admin["id"]:
        raise HTTPException(400, "Cannot deactivate yourself")

    new_status = not user.get("is_active", True)
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"is_active": new_status}})
    return {"message": f"User {'activated' if new_status else 'deactivated'}", "is_active": new_status}


@router.put("/users/{user_id}/toggle-admin")
async def toggle_admin(
    user_id: int,
    admin: dict = Depends(get_current_admin),
):
    db = get_database()
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(404, "User not found")

    new_admin = not user.get("is_admin", False)
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"is_admin": new_admin}})
    return {"message": f"Admin {'granted' if new_admin else 'revoked'}", "is_admin": new_admin}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: dict = Depends(get_current_admin),
):
    if user_id == admin["id"]:
        raise HTTPException(400, "Cannot delete yourself")
    db = get_database()
    await db.users.delete_one({"id": user_id})
    return {"message": "User deleted"}


# ── Movie Management ──────────────────────────────────────────────────────────
@router.post("/movies", response_model=MovieResponse, status_code=201)
async def create_movie(
    data: MovieCreate,
    admin: dict = Depends(get_current_admin),
):
    db = get_database()
    count = await db.movies.count_documents({})
    doc = data.model_dump()
    doc["id"] = count + 1
    doc["created_at"] = datetime.now(timezone.utc)
    res = await db.movies.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return MovieResponse.model_validate(serialize_doc(doc))


@router.put("/movies/{movie_id}", response_model=MovieResponse)
async def update_movie(
    movie_id: int,
    data: MovieUpdate,
    admin: dict = Depends(get_current_admin),
):
    db = get_database()
    movie = await db.movies.find_one({"id": movie_id})
    if not movie:
        raise HTTPException(404, "Movie not found")

    update_dict = data.model_dump(exclude_none=True)
    if update_dict:
        update_dict["updated_at"] = datetime.now(timezone.utc)
        await db.movies.update_one({"_id": movie["_id"]}, {"$set": update_dict})
        movie.update(update_dict)

    return MovieResponse.model_validate(serialize_doc(movie))


@router.delete("/movies/{movie_id}")
async def delete_movie(
    movie_id: int,
    admin: dict = Depends(get_current_admin),
):
    db = get_database()
    await db.movies.delete_one({"id": movie_id})
    return {"message": "Movie deleted"}


# ── ML Retraining ─────────────────────────────────────────────────────────────
_retrain_status = {"status": "idle", "last_run": None, "message": ""}


def _run_retrain():
    global _retrain_status
    try:
        _retrain_status["status"] = "running"
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "ml.train", "--skip-semantic"],
            capture_output=True, text=True, timeout=600
        )
        if result.returncode == 0:
            _retrain_status["status"] = "success"
            _retrain_status["message"] = "Retraining completed successfully"
        else:
            _retrain_status["status"] = "error"
            _retrain_status["message"] = result.stderr[:500]
    except Exception as e:
        _retrain_status["status"] = "error"
        _retrain_status["message"] = str(e)

    _retrain_status["last_run"] = datetime.now().isoformat()


@router.post("/retrain")
async def retrain_model(
    background_tasks: BackgroundTasks,
    admin: dict = Depends(get_current_admin),
):
    if _retrain_status["status"] == "running":
        return {"message": "Retraining already in progress", "status": _retrain_status}
    background_tasks.add_task(_run_retrain)
    return {"message": "Retraining started in background", "status": "started"}


@router.get("/retrain/status")
async def retrain_status(admin: dict = Depends(get_current_admin)):
    return _retrain_status


@router.post("/sync-tmdb")
async def trigger_tmdb_sync(
    background_tasks: BackgroundTasks,
    pages: int = Query(3, ge=1, le=10),
    admin: dict = Depends(get_current_admin),
):
    """Admin endpoint to trigger multi-industry TMDB movie import and model retraining."""
    from app.services.tmdb_sync import sync_tmdb_movies
    background_tasks.add_task(sync_tmdb_movies, max_pages_per_lang=pages)
    return {
        "message": f"TMDB multi-industry synchronization started in background ({pages} pages per language)",
        "status": "started"
    }


@router.get("/export/csv")
async def export_movies_csv(admin: dict = Depends(get_current_admin)):
    """Export movie database as CSV format."""
    from fastapi.responses import Response
    import csv, io
    db = get_database()
    movies = await db.movies.find({}).to_list(5000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "tmdb_id", "title", "release_year", "vote_average", "popularity", "genres", "original_language"])
    for m in movies:
        writer.writerow([
            m.get("id"), m.get("tmdb_id"), m.get("title"), m.get("release_year"),
            m.get("vote_average"), m.get("popularity"), ", ".join(m.get("genres") or []),
            m.get("original_language")
        ])
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=cinematch_movies.csv"})


@router.get("/export/json")
async def export_movies_json(admin: dict = Depends(get_current_admin)):
    """Export movie database as JSON format."""
    from fastapi.responses import JSONResponse
    db = get_database()
    movies = await db.movies.find({}).to_list(5000)
    cleaned = [serialize_doc(m) for m in movies]
    return JSONResponse(content=cleaned, headers={"Content-Disposition": "attachment; filename=cinematch_movies.json"})

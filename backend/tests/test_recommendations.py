import pytest
import pytest_asyncio
from app.core import database


@pytest_asyncio.fixture(autouse=True)
async def setup_test_movies():
    """Seed test database with sample movies across industries and moods."""
    db = database.get_database()
    await db.movies.delete_many({})
    test_movies = [
        {
            "id": 1, "tmdb_id": 101, "title": "RRR", "original_language": "te",
            "genres": ["Action", "Drama"], "vote_average": 8.0, "vote_count": 500, "popularity": 100.0, "weighted_rating": 8.0,
            "overview": "A passionate story of freedom fighters in India with high action battles.",
            "release_year": 2022,
        },
        {
            "id": 2, "tmdb_id": 102, "title": "Dangal", "original_language": "hi",
            "genres": ["Drama", "Biography", "Sport"], "vote_average": 8.4, "vote_count": 600, "popularity": 90.0, "weighted_rating": 8.4,
            "overview": "Inspirational true story of a wrestler training his daughters for triumph.",
            "release_year": 2016,
        },
        {
            "id": 3, "tmdb_id": 103, "title": "Vikram", "original_language": "ta",
            "genres": ["Action", "Thriller"], "vote_average": 8.2, "vote_count": 400, "popularity": 85.0, "weighted_rating": 8.2,
            "overview": "High stakes police squad investigation into a masked murder squad.",
            "release_year": 2022,
        },
        {
            "id": 4, "tmdb_id": 104, "title": "The Dark Knight", "original_language": "en",
            "genres": ["Action", "Crime", "Drama"], "vote_average": 8.5, "vote_count": 3000, "popularity": 150.0, "weighted_rating": 8.5,
            "overview": "Batman fights against gritty dark chaotic Joker in Gotham.",
            "release_year": 2008,
        },
        {
            "id": 5, "tmdb_id": 105, "title": "Spirited Away", "original_language": "ja",
            "genres": ["Animation", "Family", "Fantasy"], "vote_average": 8.5, "vote_count": 2000, "popularity": 110.0, "weighted_rating": 8.5,
            "overview": "Magic whimsical adventure of a young girl in an enchanted spirit world.",
            "release_year": 2001,
        },
        {
            "id": 6, "tmdb_id": 106, "title": "Superbad", "original_language": "en",
            "genres": ["Comedy"], "vote_average": 7.6, "vote_count": 1500, "popularity": 70.0, "weighted_rating": 7.6,
            "overview": "Hilarious goofy comedy of high school friends on a wild party night.",
            "release_year": 2007,
        },
        {
            "id": 7, "tmdb_id": 107, "title": "The Notebook", "original_language": "en",
            "genres": ["Romance", "Drama"], "vote_average": 7.8, "vote_count": 1200, "popularity": 65.0, "weighted_rating": 7.8,
            "overview": "Heartbreak love story of a passion young couple reading a journal.",
            "release_year": 2004,
        },
    ]
    await db.movies.insert_many(test_movies)


@pytest.mark.asyncio
async def test_removed_categories(client):
    """Verify Personalized Taste and Similar Movie endpoints are removed (return 404)."""
    resp_user = await client.get("/api/recommendations/user")
    assert resp_user.status_code == 404

    resp_content = await client.get("/api/recommendations/content/1")
    assert resp_content.status_code == 404


@pytest.mark.asyncio
async def test_industry_recommendations(client):
    """Verify industry endpoint returns exact regional movies without Hollywood bias."""
    industries = ["tollywood", "bollywood", "kollywood", "hollywood", "anime"]
    for ind in industries:
        resp = await client.get(f"/api/recommendations/industry/{ind}")
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendations" in data
        assert data["algorithm"] == f"industry-{ind}"

    # Verify Tollywood specifically returns RRR (Telugu)
    resp_tolly = await client.get("/api/recommendations/industry/tollywood")
    recs_tolly = resp_tolly.json()["recommendations"]
    assert len(recs_tolly) > 0
    assert recs_tolly[0]["title"] == "RRR"


@pytest.mark.asyncio
async def test_mood_recommendations(client):
    """Verify mood endpoint returns appropriate recommendations for different moods."""
    moods = ["happy", "sad", "romantic", "action", "motivational", "thriller", "comedy", "family"]
    for mood in moods:
        resp = await client.get(f"/api/recommendations/mood/{mood}")
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendations" in data
        assert data["algorithm"] == f"mood-{mood}"


@pytest.mark.asyncio
async def test_genre_recommendations(client):
    resp = await client.get("/api/recommendations/genre?genres=Action,Comedy")
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data


@pytest.mark.asyncio
async def test_popular_recommendations(client):
    resp = await client.get("/api/recommendations/popular?mode=weighted")
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data


@pytest.mark.asyncio
async def test_semantic_search(client):
    resp = await client.post("/api/recommendations/semantic", json={"query": "hilarious comedy friends", "limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data

import pytest
import pytest_asyncio
from app.core import database


@pytest_asyncio.fixture(autouse=True)
async def setup_test_search_movies():
    db = database.get_database()
    await db.movies.delete_many({})
    test_movies = [
        {
            "id": 1, "tmdb_id": 201, "title": "Inception", "original_title": "Inception",
            "genres": ["Science Fiction", "Action"], "vote_average": 8.4, "vote_count": 5000, "popularity": 120.0,
            "weighted_rating": 8.4, "overview": "A thief who steals corporate secrets through dream-sharing technology.",
            "release_year": 2010, "director": "Christopher Nolan", "cast": [{"name": "Leonardo DiCaprio"}],
            "original_language": "en"
        },
        {
            "id": 2, "tmdb_id": 202, "title": "Baahubali", "original_title": "Baahubali: The Beginning",
            "genres": ["Action", "Fantasy"], "vote_average": 8.0, "vote_count": 800, "popularity": 95.0,
            "weighted_rating": 8.0, "overview": "An adventurous and daring man becomes involved in an ancient feud.",
            "release_year": 2015, "director": "S.S. Rajamouli", "cast": [{"name": "Prabhas"}],
            "original_language": "te"
        }
    ]
    await db.movies.insert_many(test_movies)


@pytest.mark.asyncio
async def test_search_and_suggestions(client):
    # Search title
    resp = await client.get("/api/search?q=Inception")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) > 0
    assert data["items"][0]["title"] == "Inception"

    # Search director
    resp_dir = await client.get("/api/search?q=Rajamouli")
    assert resp_dir.status_code == 200
    data_dir = resp_dir.json()
    assert len(data_dir["items"]) > 0
    assert data_dir["items"][0]["title"] == "Baahubali"

    # Search industry query
    resp_ind = await client.get("/api/search?q=Tollywood")
    assert resp_ind.status_code == 200
    assert len(resp_ind.json()["items"]) > 0

    # Suggestions
    sug_resp = await client.get("/api/search/suggestions?q=Inc")
    assert sug_resp.status_code == 200
    assert isinstance(sug_resp.json(), list)

    # Trending searches
    tr_resp = await client.get("/api/search/trending-searches")
    assert tr_resp.status_code == 200
    assert isinstance(tr_resp.json(), list)

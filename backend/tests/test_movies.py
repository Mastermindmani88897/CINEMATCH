import pytest


@pytest.mark.asyncio
async def test_list_movies_empty(client):
    resp = await client.get("/api/movies/")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_genres_endpoint(client):
    resp = await client.get("/api/movies/genres")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

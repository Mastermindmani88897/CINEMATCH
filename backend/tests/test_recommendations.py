import pytest


@pytest.mark.asyncio
async def test_recommendations_endpoints(client):
    # Popular recs
    pop_resp = await client.get("/api/recommendations/popular?mode=weighted")
    assert pop_resp.status_code == 200
    assert "recommendations" in pop_resp.json()

    # Mood recs
    mood_resp = await client.get("/api/recommendations/mood/happy")
    assert mood_resp.status_code == 200
    assert "recommendations" in mood_resp.json()

    # Moods list
    moods_list = await client.get("/api/recommendations/moods")
    assert moods_list.status_code == 200
    assert "moods" in moods_list.json()

    # Semantic search endpoint
    sem_resp = await client.post("/api/recommendations/semantic", json={"query": "sci-fi space exploration", "top_k": 5})
    assert sem_resp.status_code == 200
    assert "recommendations" in sem_resp.json()

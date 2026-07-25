import pytest


@pytest.mark.asyncio
async def test_search_and_suggestions(client):
    # Search query
    resp = await client.get("/api/search?q=Inception")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data

    # Suggestions
    sug_resp = await client.get("/api/search/suggestions?q=Inc")
    assert sug_resp.status_code == 200
    assert isinstance(sug_resp.json(), list)

    # Trending searches
    tr_resp = await client.get("/api/search/trending-searches")
    assert tr_resp.status_code == 200
    assert isinstance(tr_resp.json(), list)

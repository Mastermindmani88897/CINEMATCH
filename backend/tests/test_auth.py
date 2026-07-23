import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    reg_resp = await client.post("/api/auth/register", json={
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "Password123!",
    })
    assert reg_resp.status_code == 201

    # Login
    login_resp = await client.post("/api/auth/login", json={
        "email": "testuser@example.com",
        "password": "Password123!",
    })
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "testuser@example.com"

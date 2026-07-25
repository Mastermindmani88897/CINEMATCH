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
    assert "refresh_token" in data
    assert data["user"]["email"] == "testuser@example.com"

    # Refresh token
    ref_resp = await client.post("/api/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert ref_resp.status_code == 200
    assert "access_token" in ref_resp.json()

    # Logout
    logout_resp = await client.post("/api/auth/logout")
    assert logout_resp.status_code == 200


@pytest.mark.asyncio
async def test_invalid_login(client):
    resp = await client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "WrongPassword123!",
    })
    assert resp.status_code == 401

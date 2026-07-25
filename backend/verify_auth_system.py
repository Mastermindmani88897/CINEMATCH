import asyncio
import sys
import httpx
from app.main import app
from app.core.database import init_db, get_database

sys.stdout.reconfigure(encoding='utf-8')

async def run_auth_verification():
    print("=" * 60)
    print("      CINEMATCH AI — COMPLETE AUTHENTICATION AUDIT & VERIFICATION")
    print("=" * 60)

    await init_db()
    db = get_database()

    # Generate unique credentials
    test_email = "prod_auth_user@cinematch.ai"
    test_username = "prod_auth_user"
    test_password = "Password123!"

    # Clean up existing test user if present
    await db.users.delete_many({"email": test_email})

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register User
        r_reg = await client.post("/api/auth/register", json={
            "email": test_email,
            "username": test_username,
            "password": test_password,
            "full_name": "Production Test User"
        })
        print(f"\n[1/7] Registration API: Status {r_reg.status_code} | Response: {r_reg.json()}")
        assert r_reg.status_code == 201, f"Registration failed: {r_reg.text}"

        # Verify DB insertion
        db_user = await db.users.find_one({"email": test_email})
        print(f"[1/7] MongoDB User Doc in DB: Username='{db_user['username']}', ID={db_user['id']}, Verified={db_user['is_verified']}")
        assert db_user is not None, "User not found in MongoDB!"
        assert db_user["username"] == test_username, "Username mismatch in DB!"

        # 2. Duplicate Registration Test
        r_dup = await client.post("/api/auth/register", json={
            "email": test_email,
            "username": test_username,
            "password": test_password
        })
        print(f"\n[2/7] Duplicate Registration API: Status {r_dup.status_code} | Error: {r_dup.json().get('detail')}")
        assert r_dup.status_code == 400, "Expected 400 for duplicate email!"

        # 3. Invalid Login Test
        r_inv = await client.post("/api/auth/login", json={
            "email": test_email,
            "password": "WrongPassword999!"
        })
        print(f"\n[3/7] Invalid Password Login: Status {r_inv.status_code} | Detail: {r_inv.json().get('detail')}")
        assert r_inv.status_code == 401, "Expected 401 for wrong password!"

        # 4. Valid Login Test
        r_login = await client.post("/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        print(f"\n[4/7] Valid Login API: Status {r_login.status_code}")
        login_data = r_login.json()
        access_token = login_data.get("access_token")
        refresh_token = login_data.get("refresh_token")
        print(f"  - Access Token Issued: {access_token[:25]}...")
        print(f"  - Refresh Token Issued: {refresh_token[:25]}...")
        assert access_token and refresh_token, "Tokens missing in login response!"

        # 5. Protected Endpoint /auth/me
        headers = {"Authorization": f"Bearer {access_token}"}
        r_me = await client.get("/api/auth/me", headers=headers)
        print(f"\n[5/7] Protected Route GET /auth/me: Status {r_me.status_code} | Profile Username: '{r_me.json().get('username')}'")
        assert r_me.status_code == 200, "Protected endpoint /auth/me failed!"

        # 6. Refresh Token
        r_ref = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        print(f"\n[6/7] Token Refresh API: Status {r_ref.status_code}")
        assert r_ref.status_code == 200, "Token refresh failed!"
        new_access_token = r_ref.json().get("access_token")
        assert new_access_token, "New access token missing!"

        # 7. Logout
        r_logout = await client.post("/api/auth/logout")
        print(f"\n[7/7] Logout API: Status {r_logout.status_code} | Msg: {r_logout.json().get('message')}")
        assert r_logout.status_code == 200, "Logout endpoint failed!"

    print("\n" + "=" * 60)
    print("      ALL AUTHENTICATION AUDIT TESTS PASSED SUCCESSFULLY 100%")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_auth_verification())

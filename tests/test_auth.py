import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient):
    email = "developer@example.com"
    password = "secure_password_123"

    # 1. Test Registration
    reg_resp = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert reg_resp.status_code == 201
    assert reg_resp.json()["email"] == email

    # 2. Test Login
    login_resp = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 3. Test Accessing Protected Route
    headers = {"Authorization": f"Bearer {access_token}"}
    me_resp = await client.get("/api/v1/users/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email

    # 4. Test Token Refresh
    refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    new_access_token = new_tokens["access_token"]

    # 5. Test Logout (Blacklisting)
    logout_resp = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    # 6. Test Rejected Request handling using Blacklisted token
    blocked_resp = await client.get("/api/v1/users/me", headers=headers)
    assert blocked_resp.status_code == 401

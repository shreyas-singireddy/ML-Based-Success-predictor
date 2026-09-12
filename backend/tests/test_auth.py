import pytest
from httpx import AsyncClient
from backend.app.core.config import settings
from backend.app.core.security import get_password_hash, verify_password


@pytest.mark.asyncio
async def test_argon2id_hashing():
    raw_pass = "SecureArgonPassword#2026"
    hashed = get_password_hash(raw_pass)
    assert hashed != raw_pass
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPass", hashed) is False


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    res = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "admin.test@university.edu", "password": "TestPass@123"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin.test@university.edu"
    assert data["user"]["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    res = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "admin.test@university.edu", "password": "IncorrectPassword"}
    )
    assert res.status_code == 401
    assert "error" in res.json()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    res = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "ghost@university.edu", "password": "TestPass@123"}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_endpoint(client: AsyncClient, admin_token: str):
    res = await client.get(
        f"{settings.API_V1_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin.test@university.edu"
    assert data["role"] == "ADMIN"

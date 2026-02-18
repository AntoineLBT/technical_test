import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_returns_201(client: AsyncClient):
    response = await client.post(
        "/users",
        json={"email": "user@example.com", "password": "Secure@pass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["is_active"] is False
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient):
    payload = {"email": "user@example.com", "password": "Secure@pass123"}
    await client.post("/users", json=payload)
    response = await client.post("/users", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_register_invalid_email_returns_422(client: AsyncClient):
    response = await client.post(
        "/users",
        json={"email": "not-an-email", "password": "Secure@pass123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password_returns_422(client: AsyncClient):
    response = await client.post(
        "/users",
        json={"email": "user@example.com", "password": "weak"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_password_missing_uppercase_returns_422(client: AsyncClient):
    response = await client.post(
        "/users",
        json={"email": "user@example.com", "password": "secure@pass123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_password_missing_special_char_returns_422(client: AsyncClient):
    response = await client.post(
        "/users",
        json={"email": "user@example.com", "password": "SecurePass123"},
    )
    assert response.status_code == 422

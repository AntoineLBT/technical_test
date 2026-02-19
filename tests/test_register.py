from unittest.mock import AsyncMock, patch

import pytest
from aiosmtplib import SMTPException
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
async def test_register_returns_503_on_sending_email_error(client: AsyncClient):

    with patch(
        "app.services.email_service.send", new_callable=AsyncMock
    ) as mock_email_send:
        mock_email_send.side_effect = SMTPException("")
        response = await client.post(
            "/users",
            json={"email": "user@example.com", "password": "Secure@pass123"},
        )
    assert response.status_code == 503
    assert response.json()["detail"] == "Failed to send email, please try again later"


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
@pytest.mark.parametrize(
    "password,error",
    [
        ["weak", "at least 12 characters"],
        ["secure@pass123", "at least one uppercase letter"],
        ["SecurePass123", "at least one special character"],
        ["SECURE@PASS123", "at least one lowercase letter"],
    ],
)
async def test_register_weak_password_returns_422(client: AsyncClient, password, error):
    response = await client.post(
        "/users",
        json={"email": "user@example.com", "password": password},
    )
    assert response.status_code == 422
    assert error in response.json()["detail"][0]["ctx"]["error"]

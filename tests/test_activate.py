import asyncpg
import pytest
from httpx import AsyncClient

_EMAIL = "user@example.com"
_PASSWORD = "Secure@pass123"
_PAYLOAD = {"email": _EMAIL, "password": _PASSWORD}


async def _register(client: AsyncClient) -> None:
    await client.post("/users", json=_PAYLOAD)


async def _get_latest_code(db_pool: asyncpg.Pool) -> str:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT code FROM activation_codes ORDER BY created_at DESC LIMIT 1"
        )
    assert row, "No activation code found in DB"
    return row["code"]


@pytest.mark.asyncio
async def test_activate_success(client: AsyncClient, db_pool: asyncpg.Pool):
    await _register(client)
    code = await _get_latest_code(db_pool)
    response = await client.post(
        "/users/activate", json={"code": code}, auth=(_EMAIL, _PASSWORD)
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Account activated successfully"


@pytest.mark.asyncio
async def test_activate_marks_user_active(client: AsyncClient, db_pool: asyncpg.Pool):
    await _register(client)
    code = await _get_latest_code(db_pool)
    await client.post("/users/activate", json={"code": code}, auth=(_EMAIL, _PASSWORD))

    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT is_active FROM users WHERE email = $1", _EMAIL
        )
    assert user["is_active"] is True


@pytest.mark.asyncio
async def test_activate_wrong_code_returns_422(client: AsyncClient):
    await _register(client)
    response = await client.post(
        "/users/activate", json={"code": "0000"}, auth=(_EMAIL, _PASSWORD)
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_activate_expired_code_returns_422(
    client: AsyncClient, db_pool: asyncpg.Pool
):
    await _register(client)
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE activation_codes SET expires_at = NOW() - INTERVAL '1 second'"
        )
        row = await conn.fetchrow("SELECT code FROM activation_codes LIMIT 1")

    response = await client.post(
        "/users/activate", json={"code": row["code"]}, auth=(_EMAIL, _PASSWORD)
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_activate_wrong_password_returns_401(
    client: AsyncClient, db_pool: asyncpg.Pool
):
    await _register(client)
    code = await _get_latest_code(db_pool)
    response = await client.post(
        "/users/activate", json={"code": code}, auth=(_EMAIL, "WrongPass@999")
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_activate_malformated_code_returns_422(
    client: AsyncClient, db_pool: asyncpg.Pool
):
    await _register(client)
    response = await client.post(
        "/users/activate", json={"code": "12345"}, auth=(_EMAIL, _PASSWORD)
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_activate_unknown_user_returns_401(client: AsyncClient):
    response = await client.post(
        "/users/activate",
        json={"code": "1234"},
        auth=("nobody@example.com", _PASSWORD),
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_activate_already_active_returns_409(
    client: AsyncClient, db_pool: asyncpg.Pool
):
    await _register(client)
    code = await _get_latest_code(db_pool)
    await client.post("/users/activate", json={"code": code}, auth=(_EMAIL, _PASSWORD))
    response = await client.post(
        "/users/activate", json={"code": code}, auth=(_EMAIL, _PASSWORD)
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_activate_code_cannot_be_reused(
    client: AsyncClient, db_pool: asyncpg.Pool
):
    await _register(client)
    code = await _get_latest_code(db_pool)
    await client.post("/users/activate", json={"code": code}, auth=(_EMAIL, _PASSWORD))

    # Reset is_active to isolate the replay-prevention check
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET is_active = FALSE WHERE email = $1", _EMAIL
        )

    response = await client.post(
        "/users/activate", json={"code": code}, auth=(_EMAIL, _PASSWORD)
    )
    assert response.status_code == 422

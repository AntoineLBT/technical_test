from unittest.mock import AsyncMock, patch

import asyncpg
import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.database import run_migrations
from app.dependencies import get_http_client, get_pool
from app.main import create_app


@pytest_asyncio.fixture
async def db_pool():
    """Per-test connection pool.

    Function scope ensures the pool and all fixtures that use it share the
    same event loop — avoiding asyncpg cross-loop errors with pytest-asyncio
    1.x which creates a new loop per test by default.
    Migrations are idempotent so re-running them per test is fast after the
    first run.
    """
    pool = await asyncpg.create_pool(dsn=settings.database_url)
    await run_migrations(pool)
    async with pool.acquire() as conn:
        await conn.execute(
            "TRUNCATE TABLE activation_codes, users RESTART IDENTITY CASCADE"
        )
    yield pool
    await pool.close()


@pytest.fixture(autouse=True)
def mock_email():
    """Prevent any real SMTP connection during tests."""
    with patch("app.services.email_service.send", new_callable=AsyncMock):
        yield


@pytest_asyncio.fixture
async def client(db_pool: asyncpg.Pool):
    """HTTP test client with DB pool and http client dependencies overridden.

    ASGITransport does not trigger the ASGI lifespan, so app.state is never
    populated. Both get_pool and get_http_client must be overridden to avoid
    reading from app.state at request time.
    """
    app = create_app()
    app.dependency_overrides[get_pool] = lambda: db_pool
    app.dependency_overrides[get_http_client] = lambda: httpx.AsyncClient()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

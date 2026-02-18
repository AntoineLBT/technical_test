from unittest.mock import AsyncMock, patch

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.database import run_migrations
from app.dependencies import get_pool
from app.main import create_app


@pytest_asyncio.fixture(scope="session")
async def db_pool():
    """Single connection pool shared across the whole test session."""
    pool = await asyncpg.create_pool(dsn=settings.database_url)
    await run_migrations(pool)
    yield pool
    await pool.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_db(db_pool: asyncpg.Pool):
    """Truncate all tables before each test for full isolation."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            "TRUNCATE TABLE activation_codes, users RESTART IDENTITY CASCADE"
        )


@pytest.fixture(autouse=True)
def mock_email():
    """Prevent any real SMTP connection during tests."""
    with patch("app.services.email_service.send", new_callable=AsyncMock):
        yield


@pytest_asyncio.fixture
async def client(db_pool: asyncpg.Pool):
    """HTTP test client with the DB pool dependency overridden to use the test pool."""
    app = create_app()
    app.dependency_overrides[get_pool] = lambda: db_pool

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

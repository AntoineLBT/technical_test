"""
Database connection pool and migration runner.

Migrations are plain SQL files in the migrations/ directory, named with a
numeric prefix (e.g. 001_initial.sql, 002_add_column.sql). The runner
keeps track of applied migrations in a `schema_migrations` table and only
executes files that have not been applied yet, in order.
"""

import logging
import os

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

_CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     TEXT        PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=2,
        max_size=10,
    )


async def run_migrations(pool: asyncpg.Pool, migrations_dir: str = "migrations") -> None:
    """Apply all pending SQL migration files in alphabetical order."""
    async with pool.acquire() as conn:
        # Ensure the tracking table exists (idempotent)
        await conn.execute(_CREATE_MIGRATIONS_TABLE)

        applied: set[str] = {
            row["version"]
            for row in await conn.fetch("SELECT version FROM schema_migrations")
        }

        files = sorted(
            f for f in os.listdir(migrations_dir) if f.endswith(".sql")
        )

        for filename in files:
            if filename in applied:
                logger.debug("Migration already applied: %s", filename)
                continue

            path = os.path.join(migrations_dir, filename)
            with open(path) as f:
                sql = f.read()

            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES ($1)", filename
                )

            logger.info("Applied migration: %s", filename)

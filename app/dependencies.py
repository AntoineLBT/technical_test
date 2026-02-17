from typing import AsyncGenerator

import asyncpg
import httpx
from fastapi import Depends, Request


async def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool


async def get_db(
    pool: asyncpg.Pool = Depends(get_pool),
) -> AsyncGenerator[asyncpg.Connection, None]:
    async with pool.acquire() as connection:
        yield connection


async def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client

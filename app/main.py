from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.database import create_pool, run_migrations
from app.exceptions.handlers import register_exception_handlers
from app.routers import users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    app.state.pool = await create_pool()
    await run_migrations(app.state.pool)
    app.state.http_client = httpx.AsyncClient(timeout=5.0)

    yield

    # SHUTDOWN
    await app.state.pool.close()
    await app.state.http_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="User Registration API",
        description="Dailymotion user registration with email verification",
        version="0.1.0",
        lifespan=lifespan,
    )
    register_exception_handlers(app)
    app.include_router(users.router, prefix="/users", tags=["users"])
    return app


app = create_app()

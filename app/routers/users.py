import asyncpg
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.dependencies import get_db, get_http_client
from app.schemas.user import ActivateRequest, MessageResponse, UserCreate, UserResponse
from app.services.email_service import EmailService
from app.services.user_service import UserService

router = APIRouter()
security = HTTPBasic()


def get_user_service(
    conn: asyncpg.Connection = Depends(get_db),
    http_client=Depends(get_http_client),
) -> UserService:
    return UserService(conn, EmailService())


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register_user(
    body: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.register(body.email, body.password)
    return UserResponse(id=user["id"], email=user["email"], is_active=user["is_active"])


@router.post(
    "/activate",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate account using Basic Auth + 4-digit code",
)
async def activate_user(
    body: ActivateRequest,
    credentials: HTTPBasicCredentials = Depends(security),
    conn: asyncpg.Connection = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    async with conn.transaction():
        await service.activate(credentials, body.code)
    return MessageResponse(message="Account activated successfully")

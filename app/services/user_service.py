import bcrypt
from asyncpg import Connection, Record, UniqueViolationError
from fastapi.security import HTTPBasicCredentials

from app.exceptions.base import (
    InvalidCodeError,
    InvalidCredentialsError,
    UserAlreadyActiveError,
    UserAlreadyExistsError,
)
from app.repositories.code_repository import CodeRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService


class UserService:
    def __init__(self, conn: Connection, email_service: EmailService) -> None:
        self._users_repo = UserRepository(conn)
        self._codes_repo = CodeRepository(conn)
        self._email_service = email_service

    async def register(self, email: str, password: str) -> Record:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            user = await self._users_repo.create(email, password_hash)
        except UniqueViolationError:
            raise UserAlreadyExistsError()

        code = await self._codes_repo.create_for_user(user["id"])
        await self._email_service.send_activation_code(email, code)

        return user

    async def activate(self, credentials: HTTPBasicCredentials, code: str) -> None:
        user = await self._users_repo.get_by_email(credentials.username)

        if user is None:
            raise InvalidCredentialsError()

        # bcrypt.checkpw is constant-time — prevents timing attacks
        password_valid = bcrypt.checkpw(
            credentials.password.encode(),
            user["password_hash"].encode(),
        )
        if not password_valid:
            raise InvalidCredentialsError()

        if user["is_active"]:
            raise UserAlreadyActiveError()

        code_record = await self._codes_repo.get_lastest_valid(user["id"], code)
        if code_record is None:
            raise InvalidCodeError()

        await self._codes_repo.mark_used(code_record["id"])
        await self._users_repo.activate(user["id"])

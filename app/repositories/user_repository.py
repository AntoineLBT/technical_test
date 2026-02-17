from uuid import UUID

from asyncpg import Connection, Record


class UserRepository:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    async def create(self, email: str, password_hash: str) -> Record:
        """Insert a new user and return the created record.

        Raises asyncpg.UniqueViolationError if the email already exists.
        The caller is responsible for mapping this to a domain exception.
        """
        record = await self._conn.fetchrow(
            """
            INSERT INTO users (email, password_hash)
            VALUES ($1, $2)
            RETURNING id, email, is_active, created_at
            """,
            email,
            password_hash,
        )
        assert record
        return record

    async def get_by_email(self, email: str) -> Record | None:
        return await self._conn.fetchrow(
            "SELECT id, email, password_hash, is_active FROM users WHERE email = $1",
            email,
        )

    async def activate(self, user_id: UUID) -> None:
        await self._conn.execute(
            """
            UPDATE users
            SET is_active = TRUE, updated_at = NOW()
            WHERE id = $1
            """,
            user_id,
        )

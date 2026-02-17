from secrets import randbelow
from uuid import UUID

from asyncpg import Connection, Record


def _generate_code() -> str:
    """Generate a cryptographically secure 4-digit code (zero-padded)."""
    return str(randbelow(10_000)).zfill(4)


class CodeRepository:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    async def create_for_user(self, user_id: UUID) -> str:
        """Insert a new activation code and return its value.

        expiry is computed DB-side to avoid clock drift between app instances.
        """
        code = _generate_code()
        await self._conn.execute(
            """
            INSERT INTO activation_codes (user_id, code, expires_at)
            VALUES ($1, $2, NOW() + INTERVAL '1 minute')
            """,
            user_id,
            code,
        )
        return code

    async def get_lastest_valid(self, user_id: UUID, code: str) -> Record | None:
        """Return the most recent unused, non-expired code record matching user + code.

        Returns None if no such record exists (wrong code, expired, or already used).
        """
        return await self._conn.fetchrow(
            """
            SELECT id, user_id, code, expires_at, used_at
            FROM activation_codes
            WHERE user_id   = $1
              AND code       = $2
              AND expires_at > NOW()
              AND used_at   IS NULL
            ORDER BY created_at DESC
            LIMIT 1
            """,
            user_id,
            code,
        )

    async def mark_used(self, code_id: UUID) -> None:
        await self._conn.execute(
            "UPDATE activation_codes SET used_at = NOW() WHERE id = $1",
            code_id,
        )

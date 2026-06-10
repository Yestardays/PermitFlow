import json
from datetime import UTC, datetime, timedelta
from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool


class MemorySessionStore:
    def __init__(self, ttl_minutes: int = 30):
        self.ttl = timedelta(minutes=ttl_minutes)
        self._data: dict[str, tuple[datetime, dict[str, Any]]] = {}

    async def get(self, thread_id: str) -> dict[str, Any] | None:
        entry = self._data.get(thread_id)
        if not entry:
            return None
        expires_at, value = entry
        if expires_at <= datetime.now(UTC):
            self._data.pop(thread_id, None)
            return None
        return value

    async def set(self, thread_id: str, value: dict[str, Any]) -> None:
        self._data[thread_id] = (datetime.now(UTC) + self.ttl, value)

    async def delete(self, thread_id: str) -> None:
        self._data.pop(thread_id, None)


class PostgresSessionStore:
    def __init__(self, pool: AsyncConnectionPool, ttl_minutes: int = 30):
        self.pool = pool
        self.ttl = timedelta(minutes=ttl_minutes)

    async def get(self, thread_id: str) -> dict[str, Any] | None:
        async with self.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("DELETE FROM application_sessions WHERE expires_at <= now()")
            await cur.execute(
                "SELECT state FROM application_sessions WHERE thread_id = %s",
                (thread_id,),
            )
            row = await cur.fetchone()
            return row["state"] if row else None

    async def set(self, thread_id: str, value: dict[str, Any]) -> None:
        expires_at = datetime.now(UTC) + self.ttl
        async with self.pool.connection() as conn:
            await conn.execute(
                """INSERT INTO application_sessions(thread_id,state,expires_at)
                   VALUES (%s,%s,%s)
                   ON CONFLICT(thread_id) DO UPDATE SET state=excluded.state,
                   expires_at=excluded.expires_at, updated_at=now()""",
                (thread_id, json.dumps(value, ensure_ascii=False), expires_at),
            )

    async def delete(self, thread_id: str) -> None:
        async with self.pool.connection() as conn:
            await conn.execute(
                "DELETE FROM application_sessions WHERE thread_id = %s", (thread_id,)
            )

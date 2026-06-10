import json
from collections.abc import Awaitable, Callable, Sequence

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from permitflow.models import PermissionItem

Embedder = Callable[[str], Awaitable[list[float]]]


def embedding_text(item: PermissionItem) -> str:
    return "\n".join(
        filter(
            None,
            [
                item.name,
                item.category,
                item.description,
                "别名：" + "、".join(item.aliases),
            ],
        )
    )


def _contains(item: PermissionItem, query: str) -> bool:
    needle = query.casefold().strip()
    return bool(needle) and any(
        needle in value.casefold() or value.casefold() in needle
        for value in [item.name, *item.aliases]
    )


class MemoryKnowledgeRepository:
    def __init__(self, items: Sequence[PermissionItem]):
        self.items = list(items)

    async def search(self, query: str, limit: int = 5) -> list[PermissionItem]:
        exact = [item for item in self.items if _contains(item, query)]
        if exact:
            return exact[:limit]
        tokens = {part.casefold() for part in query.split() if part}

        def score(item: PermissionItem) -> int:
            haystack = f"{item.name} {item.category} {' '.join(item.aliases)}".casefold()
            category_match = item.category.casefold() in query.casefold()
            return int(category_match) + sum(token in haystack for token in tokens)

        ranked = sorted(
            self.items,
            key=score,
            reverse=True,
        )
        return [item for item in ranked if score(item) > 0][:limit]


class PostgresKnowledgeRepository:
    def __init__(self, pool: AsyncConnectionPool, embedder: Embedder | None = None):
        self.pool = pool
        self.embedder = embedder

    async def search(self, query: str, limit: int = 5) -> list[PermissionItem]:
        exact_sql = """
            SELECT * FROM permission_items
            WHERE name ILIKE %(pattern)s
               OR EXISTS (
                   SELECT 1 FROM jsonb_array_elements_text(aliases) a
                   WHERE a ILIKE %(pattern)s
               )
            LIMIT %(limit)s
        """
        async with self.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(exact_sql, {"pattern": f"%{query}%", "limit": limit})
            rows = await cur.fetchall()
            if rows:
                return [self._to_item(row) for row in rows]
            if not self.embedder:
                return []
            embedding = await self.embedder(query)
            await cur.execute(
                "SELECT * FROM permission_items WHERE embedding IS NOT NULL "
                "ORDER BY embedding <=> %(embedding)s::vector LIMIT %(limit)s",
                {"embedding": json.dumps(embedding), "limit": limit},
            )
            return [self._to_item(row) for row in await cur.fetchall()]

    @staticmethod
    def _to_item(row: dict) -> PermissionItem:
        allowed = set(PermissionItem.model_fields)
        return PermissionItem.model_validate(
            {key: value for key, value in row.items() if key in allowed}
        )

    async def log_unmatched(self, open_id: str, user_input: str, inferred: dict) -> None:
        async with self.pool.connection() as conn:
            await conn.execute(
                "INSERT INTO unmatched_requests(open_id,user_input,inferred_intent) "
                "VALUES (%s,%s,%s)",
                (open_id, user_input[:500], json.dumps(inferred, ensure_ascii=False)),
            )

    async def list_items(self) -> list[PermissionItem]:
        async with self.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("SELECT * FROM permission_items ORDER BY category, name")
            return [self._to_item(row) for row in await cur.fetchall()]

    async def upsert(self, item: PermissionItem) -> PermissionItem:
        payload = item.model_dump(mode="json", exclude={"id"})
        embedding = await self.embedder(embedding_text(item)) if self.embedder else None
        async with self.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """INSERT INTO permission_items
                   (name,category,jira_project_key,issue_type,approver_group,required_fields,
                    prerequisites,validity_options,aliases,sensitive,description,embedding)
                   VALUES (%(name)s,%(category)s,%(jira_project_key)s,%(issue_type)s,
                           %(approver_group)s,%(required_fields)s,%(prerequisites)s,
                           %(validity_options)s,%(aliases)s,%(sensitive)s,%(description)s,
                           %(embedding)s::vector)
                   ON CONFLICT(name) DO UPDATE SET category=excluded.category,
                     jira_project_key=excluded.jira_project_key, issue_type=excluded.issue_type,
                     approver_group=excluded.approver_group,
                     required_fields=excluded.required_fields,
                     prerequisites=excluded.prerequisites,
                     validity_options=excluded.validity_options, aliases=excluded.aliases,
                     sensitive=excluded.sensitive, description=excluded.description,
                     embedding=excluded.embedding,
                     updated_at=now()
                   RETURNING *""",
                {
                    **payload,
                    "required_fields": json.dumps(payload["required_fields"], ensure_ascii=False),
                    "prerequisites": json.dumps(payload["prerequisites"], ensure_ascii=False),
                    "validity_options": json.dumps(payload["validity_options"], ensure_ascii=False),
                    "aliases": json.dumps(payload["aliases"], ensure_ascii=False),
                    "embedding": json.dumps(embedding) if embedding is not None else None,
                },
            )
            return self._to_item(await cur.fetchone())

    async def index_embeddings(self) -> int:
        if not self.embedder:
            raise RuntimeError("embedding client is not configured")
        items = await self.list_items()
        async with self.pool.connection() as conn:
            for item in items:
                embedding = await self.embedder(embedding_text(item))
                await conn.execute(
                    "UPDATE permission_items SET embedding = %s::vector, updated_at = now() "
                    "WHERE id = %s",
                    (json.dumps(embedding), item.id),
                )
        return len(items)

    async def delete(self, item_id: int) -> bool:
        async with self.pool.connection() as conn, conn.cursor() as cur:
            await cur.execute("DELETE FROM permission_items WHERE id = %s", (item_id,))
            return cur.rowcount > 0

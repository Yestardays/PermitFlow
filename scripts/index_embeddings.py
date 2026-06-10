import asyncio

from openai import AsyncOpenAI
from psycopg_pool import AsyncConnectionPool

from permitflow.config import get_settings
from permitflow.knowledge import PostgresKnowledgeRepository
from permitflow.llm import EmbeddingClient


async def main() -> None:
    settings = get_settings()
    client = AsyncOpenAI(
        api_key=settings.embedding_api_key,
        base_url=settings.embedding_base_url,
    )
    embedder = EmbeddingClient(
        client,
        settings.embedding_model,
        settings.embedding_dimensions,
    )
    pool = AsyncConnectionPool(settings.database_url, open=False)
    await pool.open()
    try:
        count = await PostgresKnowledgeRepository(pool, embedder.embed).index_embeddings()
    finally:
        await pool.close()
        await client.close()
    print(f"indexed {count} permission items")


if __name__ == "__main__":
    asyncio.run(main())

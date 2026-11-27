"""Redis queue for background ingestion jobs."""

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings


def redis_settings(redis_url: str) -> RedisSettings:
    """Convert a Redis URL into ARQ connection settings."""
    return RedisSettings.from_dsn(redis_url)


class Queue:
    """Send document ingestion jobs to Redis."""

    def __init__(self, redis: ArqRedis) -> None:
        self.redis = redis

    @classmethod
    async def connect(cls, redis_url: str) -> "Queue":
        redis = await create_pool(redis_settings(redis_url))
        return cls(redis)

    async def put(self, item_ids: list[int]) -> int:
        """Queue items and return the number of newly queued jobs."""
        count = 0

        for item_id in item_ids:
            job = await self.redis.enqueue_job(
                "ingest_document",
                item_id,
                _job_id=f"ingest:{item_id}",
            )
            if job is not None:
                count += 1

        return count

    async def close(self) -> None:
        await self.redis.aclose()

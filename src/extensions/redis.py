from fastapi import Query
import redis.asyncio as redis
from src.config import settings


def init():
    async def AsyncClient():
        client = redis.Redis.from_url(str(settings.REDIS_URI))
        return client

    async def get_async_redis(
        auto_close: bool = Query(default=True, include_in_schema=False)
    ):
        try:
            client = await AsyncClient()
            yield client
        finally:
            if auto_close:
                await client.aclose()

    return get_async_redis

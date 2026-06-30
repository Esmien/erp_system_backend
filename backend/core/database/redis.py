from redis.asyncio import Redis

from backend.core.config import settings

# Инициализация подключений к Redis
redis_client = Redis.from_url(url=settings.redis.redis_url, decode_responses=True)


def get_redis() -> Redis:
    """Провайдер для Dependency Injection в FastAPI"""
    if redis_client is None:
        raise RuntimeError("Клиент Redis не инициализирован")
    return redis_client


async def close_redis() -> None:
    if redis_client:
        await redis_client.close()

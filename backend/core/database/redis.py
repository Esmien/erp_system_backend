from redis.asyncio import Redis, from_url

from backend.core.config import settings

# Глобальная переменная для хранения пула соединений
redis_client: Redis | None = None


async def init_redis() -> None:
    """Инициализирует подключение к Redis"""
    global redis_client
    redis_client = from_url(settings.redis.redis_url, encoding="utf-8", decode_responses=True)


def get_redis() -> Redis:
    """Провайдер для Dependency Injection в FastAPI"""
    if redis_client is None:
        raise RuntimeError("Клиент Redis не инициализирован")
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()

from redis.asyncio import Redis

from backend.core.config import settings

# Инициализация подключений к Redis
redis_client = Redis.from_url(url=settings.redis.redis_url, decode_responses=True)
redis_client_config = Redis.from_url(url=settings.redis.redis_config_url, decode_responses=True)


def get_redis() -> Redis:
    """Провайдер для Dependency Injection в FastAPI"""
    if redis_client is None:
        raise RuntimeError("Клиент Redis не инициализирован")
    return redis_client


def get_config_redis() -> Redis:
    if redis_client_config is None:
        raise RuntimeError("Конфигурационный клиент Redis не инициализирован")
    return redis_client_config


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()
    if redis_client_config:
        await redis_client_config.close

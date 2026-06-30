from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from backend.core.database.redis import get_config_redis, get_redis

RedisDepends = Annotated[Redis, Depends(get_redis)]
RedisConfigDepends = Annotated[Redis, Depends(get_config_redis)]

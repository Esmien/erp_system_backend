from collections.abc import Callable
from functools import wraps
from typing import Any

from loguru import logger

from backend.rbac.schemas import AccessRuleDTO


def rbac_cache(ttl: int = 3600) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            self: Any, role_id: int, business_element_name: str
        ) -> AccessRuleDTO | None:
            # Формируем ключ напрямую из аргументов
            cache_key = f"rbac:rule:{role_id}:{business_element_name}"

            # Проверяем кэш
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                logger.debug(
                    f"CACHED: Правило {cached_data} получено для роли {role_id} к {business_element_name}."
                )
                return AccessRuleDTO.model_validate_json(cached_data)

            # Вызываем оригинальный метод, если был промах
            result = await func(self, role_id, business_element_name)
            logger.debug(f"MISS: Кэш для правило {cached_data} не найден.")
            # Кэшируем результат
            if result:
                await self.redis.setex(
                    name=cache_key, time=ttl, value=result.model_dump_json()
                )
                logger.debug(f"SET: Кэш для правила {cached_data} установлен.")
            return result

        return wrapper

    return decorator

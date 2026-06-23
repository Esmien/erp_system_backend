import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi.concurrency import run_in_threadpool
from loguru import logger

from backend.core.config import settings
from backend.exceptions import InvalidPasswordError


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, совпадает ли пароль с хешем

    Args:
        plain_password - Пароль в открытом виде
        hashed_password - Хеш пароля

    Returns:
        True если пароль верный

    Raises:
        InvalidPasswordError - если пароль неверный
    """

    # Превращаем пароль в набор байтов
    password_bytes = plain_password.encode(encoding="utf-8")
    # Превращаем хеш пароля в набор байтов
    hashed_password_bytes = hashed_password.encode(encoding="utf-8")
    # Сравниваем байты
    is_password_valid = await run_in_threadpool(bcrypt.checkpw, password_bytes, hashed_password_bytes)

    if not is_password_valid:
        raise InvalidPasswordError

    return is_password_valid


async def get_password_hash(password: str) -> str:
    """
    Генерирует хеш пароля

    Args:
        password - Пароль в открытом виде

    Returns:
        Хеш пароля
    """

    # Превращаем пароль в набор байтов
    password_bytes = password.encode(encoding="utf-8")

    # Генерируем соль
    salt = bcrypt.gensalt()
    hashed_password = await run_in_threadpool(bcrypt.hashpw, password_bytes, salt)

    # Возвращаем хеш в виде строки
    return hashed_password.decode("utf-8")


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Создает JWT токен.

    Args:
        data - Данные, которые мы хотим зашить в токен (например, {"sub": "user_email"})
        expires_delta - Время жизни токена. Если не передано, берем дефолтное

    Returns:
        Закодированный токен
    """

    # Спасаем исходный словарь от мутаций
    curr_data = data.copy()
    expires_time = datetime.now(tz=UTC)

    # Если время жизни токена не задано, берем дефолтное
    if expires_delta:
        expires_time += expires_delta
    else:
        expires_time += timedelta(minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES)

    logger.debug(f"Время жизни токена: {expires_time}")

    # Добавляем время жизни и ID токена в словарь
    curr_data["exp"] = expires_time
    curr_data["jti"] = str(uuid.uuid4())

    # Собираем токен со всеми необходимыми данными
    return jwt.encode(
        payload=curr_data,
        key=settings.security.SECRET_KEY,
        algorithm=settings.security.ALGORITHM,
    )

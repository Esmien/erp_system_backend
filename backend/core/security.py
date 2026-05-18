import bcrypt
from datetime import datetime, timedelta, timezone

import jwt
from loguru import logger
from fastapi.concurrency import run_in_threadpool

from backend.core.config import settings
from backend.exceptions import InvalidPasswordError


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, совпадает ли пароль с хешем

    Args:
        plain_password - Пароль в открытом виде
        hashed_password - Хеш пароля

    Returns:
        True, если пароль совпадает с хешем, иначе False
    """

    # Превращаем пароль в набор байтов
    password_bytes = plain_password.encode("utf-8")
    # Превращаем хеш пароля в набор байтов
    hashed_password_bytes = hashed_password.encode("utf-8")
    is_password_valid = await run_in_threadpool(
        bcrypt.checkpw, password_bytes, hashed_password_bytes
    )

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
    password_bytes = password.encode("utf-8")

    # Генерируем соль
    salt = bcrypt.gensalt()
    hashed_password = await run_in_threadpool(bcrypt.hashpw, password_bytes, salt)

    # Возвращаем хеш в виде строки
    return hashed_password.decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
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
    expires_time = datetime.now(timezone.utc)

    # Если время жизни токена не задано, берем дефолтное
    if expires_delta:
        expires_time += expires_delta
    else:
        expires_time += timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    logger.debug(f"Время жизни токена: {expires_time}")

    # Добавляем время жизни токена в словарь
    curr_data["exp"] = expires_time

    return jwt.encode(curr_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

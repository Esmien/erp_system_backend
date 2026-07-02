from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.api.dependencies.redis import RedisDepends
from backend.api.dependencies.reg_and_auth import AuthServiceDepends
from backend.core.config import settings
from backend.exceptions import (
    UserDoesNotExistError,
    UserNotActiveError,
)
from backend.user.schemas import UserDTO

# Для аутентификации принимаем токен напрямую
security = HTTPBearer()

CredentialsDepends = Annotated[HTTPAuthorizationCredentials, Depends(security)]


async def get_current_user(
    auth_service: AuthServiceDepends,
    redis: RedisDepends,
    credentials: CredentialsDepends,
) -> UserDTO:
    """
    Возвращает текущего активного пользователя по JWT токену

    Args:
        auth_service - сервисный модуль для работы с аутентификацией
        redis - DI Redis для проверки JWT на наличие в блэклисте
        credentials - объект, содержащий извлеченный из заголовков запроса JWT-токен

    Returns:
        Модель текущего авторизованного пользователя

    Raises:
        HTTPException(401) - при невалидном JWT
    """
    # Локальное кастомное исключение для невалидного токена
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ошибка валидации токена",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Достаем токен из заголовка
    token = credentials.credentials

    # Декодируем токен и проверяем его валидность и вытаскиваем id пользователя
    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.security.SECRET_KEY,
            algorithms=[settings.security.ALGORITHM],
        )

        if payload.get("type") != "access":
            raise credentials_exception

        user_id = payload.get("sub")
        jti = payload.get("jti")

        if user_id is None:
            raise credentials_exception

        # Проверяем токен на наличие в блэклисте
        if jti:
            redis_key = settings.redis_keys.key_jwt_blacklist(jti=jti)
            is_revoked = await redis.get(redis_key)
            if is_revoked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Токен отозван. Пожалуйста, авторизуйтесь заново.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    except jwt.InvalidTokenError:
        raise credentials_exception from None

    # Проверяем, активен ли пользователь (is_active=True)
    try:
        user = await auth_service.get_active_user_by_id(user_id=int(user_id))
        return user
    except (UserDoesNotExistError, UserNotActiveError):
        raise credentials_exception from None


CurrentUserDepends = Annotated[UserDTO, Depends(get_current_user)]

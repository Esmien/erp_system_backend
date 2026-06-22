from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.api.dependencies.reg_and_auth import AuthServiceDepends
from backend.core.config import settings
from backend.exceptions import (
    UserDoesNotExistError,
    UserNotActiveError,
)
from backend.user.schemas import UserDTO

# Извлекает Bearer-токен из заголовка Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    auth_service: AuthServiceDepends,
    token: str = Depends(oauth2_scheme),
) -> UserDTO:
    """
    Возвращает текущего активного пользователя по JWT токену

    Args:
        token - JWT токен пользователя
        auth_service - сервисный модуль для работы с аутентификацией

    Returns:
        Модель текущего авторизованного пользователя

    Raises:
        HTTPException(401) - при невалидном JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ошибка валидации токена",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Декодируем токен и проверяем его валидность и вытаскиваем id пользователя
    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.security.SECRET_KEY,
            algorithms=[settings.security.ALGORITHM],
        )
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception from None

    # Проверяем, активен ли пользователь (is_active=True)
    try:
        user = await auth_service.get_active_user_by_id(user_id=int(user_id))
        return user
    except (UserDoesNotExistError, UserNotActiveError):
        raise credentials_exception from None


CurrentUserDepends = Annotated[UserDTO, Depends(get_current_user)]

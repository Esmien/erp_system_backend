from typing import Annotated

from fastapi import Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.engine import get_session
from backend.core.database.repository.user import UserRepository
from backend.core.schemas.user import UserUpdate
from backend.core.services.user_service import UserService


async def get_user_repo(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    """
    Провайдер репозитория для работы с пользователями для инъекции в другие зависимости

    Args:
        session - сессия подключения к БД из пула

    Returns:
        Инстанс репозитория пользователей с проброшенной сессией
    """
    return UserRepository(session)


async def get_user_service(
    repo: UserRepository = Depends(get_user_repo),
) -> UserService:
    """
    Провайдер сервиса пользователей для инъекции в Annotated

    Args:
        repo - репозиторий пользователей с проброшенной сессией

    Returns:
        Инстанс сервиса пользователей проброшенным репозиторием
    """
    return UserService(repo=repo)


# Готовые DI для использования в роутерах
UserServiceDepends = Annotated[UserService, Depends(get_user_service)]

UserUpdateBody = Annotated[UserUpdate, Body()]

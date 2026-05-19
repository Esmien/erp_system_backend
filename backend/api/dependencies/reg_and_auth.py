from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.engine import get_session
from backend.core.database.repository.reg_and_auth import (
    RegisterRepository,
    AuthRepository,
)
from backend.core.services.auth_service import AuthService, RegisterService


async def get_register_repo(
    session: AsyncSession = Depends(get_session),
) -> RegisterRepository:
    """
    Провайдер репозитория регистрации для инъекции в другие зависимости

    Args:
        session - сессия подключения к БД из пула

    Returns:
        Инстанс репозитория регистрации с проброшенной сессией
    """
    return RegisterRepository(session)


async def get_auth_repo(
    session: AsyncSession = Depends(get_session),
) -> AuthRepository:
    """
    Провайдер репозитория аутентификации для инъекции в другие зависимости

    Args:
        session - сессия подключения к БД из пула

    Returns:
        Инстанс репозитория RBAC с проброшенной сессией
    """
    return AuthRepository(session)


async def get_auth_service(
    repo: AuthRepository = Depends(get_auth_repo),
) -> AuthService:
    """
    Провайдер сервиса аутентификации для инъекции в Annotated

    Args:
        repo - репозиторий аутентификации с проброшенной сессией

    Returns:
        Инстанс сервиса аутентификации проброшенным репозиторием
    """
    return AuthService(repo=repo)


async def get_register_service(
    repo: RegisterRepository = Depends(get_register_repo),
) -> RegisterService:
    """
    Провайдер сервиса регистрации для инъекции в Annotated

    Args:
        repo - репозиторий регистрации с проброшенной сессией

    Returns:
        Инстанс сервиса регистрации проброшенным репозиторием
    """
    return RegisterService(repo=repo)


# Готовые DI для использования в роутерах
AuthFormDepends = Annotated[OAuth2PasswordRequestForm, Depends()]

AuthServiceDepends = Annotated[AuthService, Depends(get_auth_service)]

RegisterServiceDepends = Annotated[RegisterService, Depends(get_register_service)]

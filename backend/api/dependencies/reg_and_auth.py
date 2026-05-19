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
    """Провайдер репозитория для инъекции в роутеры"""
    return RegisterRepository(session)


async def get_auth_repo(
    session: AsyncSession = Depends(get_session),
) -> AuthRepository:
    """Провайдер репозитория для инъекции в роутеры"""
    return AuthRepository(session)


async def get_auth_service(
    repo: AuthRepository = Depends(get_auth_repo),
) -> AuthService:
    return AuthService(repo=repo)


async def get_register_service(
    repo: RegisterRepository = Depends(get_register_repo),
) -> RegisterService:
    return RegisterService(repo=repo)


AuthFormDepends = Annotated[OAuth2PasswordRequestForm, Depends()]

AuthServiceDepends = Annotated[AuthService, Depends(get_auth_service)]

RegisterServiceDepends = Annotated[RegisterService, Depends(get_register_service)]

from typing import Annotated

from fastapi import Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies.permissions import get_current_user
from backend.core.database.engine import get_session
from backend.core.database.models import User
from backend.core.database.repository.user import UserRepository
from backend.core.schemas.user import UserUpdate
from backend.core.services.user_service import UserService


async def get_user_repo(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    """Провайдер репозитория для инъекции в роутеры"""
    return UserRepository(session)


async def get_user_service(
    repo: UserRepository = Depends(get_user_repo),
) -> UserService:
    return UserService(repo=repo)


CurrentUserDepends = Annotated[User, Depends(get_current_user)]

UserServiceDepends = Annotated[UserService, Depends(get_user_service)]

UserUpdateBody = Annotated[UserUpdate, Body()]

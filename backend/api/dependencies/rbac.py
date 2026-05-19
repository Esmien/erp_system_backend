from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.engine import get_session
from backend.core.database.repository.rbac import RbacRepository
from backend.core.services.rbac_service import RbacService


async def get_rbac_repo(
    session: AsyncSession = Depends(get_session),
) -> RbacRepository:
    """
    Провайдер репозитория RBAC для инъекции в другие зависимости

    Args:
        session - сессия подключения к БД из пула

    Returns:
        Инстанс репозитория RBAC с проброшенной сессией
    """
    return RbacRepository(session=session)


async def get_rbac_service(
    repo: RbacRepository = Depends(get_rbac_repo),
) -> RbacService:
    """
    Провайдер сервиса RBAC для инъекции в Annotated

    Args:
        repo - репозиторий RBAC с проброшенной сессией

    Returns:
        Инстанс сервиса RBAC с проброшенным репозиторием
    """
    return RbacService(repo=repo)


# Готовая DI для использования в роутерах
RbacServiceDepends = Annotated[RbacService, Depends(get_rbac_service)]

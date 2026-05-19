from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.engine import get_session
from backend.core.database.repository.rbac import RbacRepository
from backend.core.services.rbac_service import RbacService


async def get_rbac_repo(
    session: AsyncSession = Depends(get_session),
) -> RbacRepository:
    """Провайдер репозитория для инъекции в роутеры"""
    return RbacRepository(session)


async def get_rbac_service(
    repo: RbacRepository = Depends(get_rbac_repo),
) -> RbacService:
    return RbacService(repo=repo)


RbacServiceDepends = Annotated[RbacService, Depends(get_rbac_service)]

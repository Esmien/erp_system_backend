from typing import Annotated

from fastapi import Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.engine import get_session
from backend.core.database.repository.team import TeamRepository
from backend.core.schemas.team import TeamCreate, TeamJoin
from backend.core.services.team_service import TeamService


async def get_team_repo(
    session: AsyncSession = Depends(get_session),
) -> TeamRepository:
    """
    Провайдер репозитория для работы с командами для инъекции в другие зависимости

    Args:
        session - сессия подключения к БД из пула

    Returns:
        Инстанс репозитория команд с проброшенной сессией
    """
    return TeamRepository(session)


async def get_team_service(
    repo: TeamRepository = Depends(get_team_repo),
) -> TeamService:
    """
    Провайдер сервиса для работы с командами для инъекции в Annotated

    Args:
        repo - репозиторий команд с проброшенной сессией

    Returns:
        Инстанс сервиса команд проброшенным репозиторием
    """
    return TeamService(repo=repo)


# Готовые DI для использования в роутерах
TeamServiceDepends = Annotated[TeamService, Depends(get_team_service)]

TeamCreateBody = Annotated[TeamCreate, Body()]

TeamJoinQuery = Annotated[TeamJoin, Query()]

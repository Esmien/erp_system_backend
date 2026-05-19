from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.engine import get_session
from backend.core.database.repository.team import TeamRepository
from backend.core.schemas.team import TeamCreate, TeamJoin
from backend.core.services.team_service import TeamService


async def get_team_repo(
    session: AsyncSession = Depends(get_session),
) -> TeamRepository:
    """Провайдер репозитория для инъекции в роутеры"""
    return TeamRepository(session)


async def get_team_service(
    repo: TeamRepository = Depends(get_team_repo),
) -> TeamService:
    return TeamService(repo=repo)


TeamServiceDepends = Annotated[TeamService, Depends(get_team_service)]

TeamCreateQuery = Annotated[TeamCreate, Query()]

TeamJoinQuery = Annotated[TeamJoin, Query()]

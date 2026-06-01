from typing import Annotated

from fastapi import Depends, Body

from backend.api.dependencies.rbac import RbacServiceDepends
from backend.api.dependencies.uow import UowDepends
from backend.team.schemas import TeamCreate, TeamJoin
from backend.team.service import TeamService


def get_team_service(uow: UowDepends, rbac_service: RbacServiceDepends) -> TeamService:
    """Провайдер сервиса для работы с командами для инъекции в Annotated"""
    return TeamService(uow=uow, rbac_service=rbac_service)


# Готовые DI для использования в роутерах
TeamServiceDepends = Annotated[TeamService, Depends(get_team_service)]
TeamCreateBody = Annotated[TeamCreate, Body()]
TeamJoinBody = Annotated[TeamJoin, Body()]

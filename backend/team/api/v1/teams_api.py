from fastapi import APIRouter, Depends, status

from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.rbac.api.permissions_dependencies import (
    CurrentUserDepends,
    get_current_user,
)
from backend.team.api.teams_dependencies import (
    TeamCreateBody,
    TeamJoinBody,
    TeamServiceDepends,
)
from backend.team.schemas import TeamRead, TeamWithMembersRead

router = APIRouter(prefix="/teams", tags=["Команды"], dependencies=[Depends(get_current_user)])


@router.get(
    path="/{team_id}/",
    response_model=TeamWithMembersRead,
    status_code=status.HTTP_200_OK,
    summary="Получить информацию о команде",
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для просмотра этой команды",
        },
        404: {"model": ErrorResponseSchema, "description": "Команда не найдена"},
    },
)
async def get_team(
    team_id: int,
    service: TeamServiceDepends,
    current_user: CurrentUserDepends,
):
    """
    Возвращает данные команды и список её участников
    """
    team = await service.get_team(team_id=team_id, user=current_user)
    return team


@router.post(
    path="/",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую команду",
    responses={
        400: {
            "model": ErrorResponseSchema,
            "description": "Команда с таким названием уже существует",
        },
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для создания команды",
        },
    },
)
async def create_team(
    service: TeamServiceDepends,
    team_in: TeamCreateBody,
    current_user: CurrentUserDepends,
):
    """
    Создает новую пустую команду
    """
    team = await service.create_team(team_in=team_in, user=current_user)
    return team


@router.post(
    path="/join/",
    response_model=TeamRead,
    status_code=status.HTTP_200_OK,
    summary="Присоединиться к команде по коду",
    responses={
        400: {
            "model": ErrorResponseSchema,
            "description": "Попытка повторно вступить в команду",
        },
        404: {
            "model": ErrorResponseSchema,
            "description": "Команда не найдена по инвайт-коду",
        },
    },
)
async def join_team(
    join_data: TeamJoinBody,
    service: TeamServiceDepends,
    current_user: CurrentUserDepends,
):
    """
    Привязывает пользователя к команде по 6-значному коду приглашения.
    """
    team = await service.join_team(user=current_user, invite_code=join_data.invite_code)
    return team

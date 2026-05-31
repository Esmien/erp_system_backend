from fastapi import APIRouter, status, Depends

from backend.api.dependencies.permissions import (
    PermissionChecker,
    CurrentUserDepends,
    get_current_user,
)
from backend.api.dependencies.teams import (
    TeamServiceDepends,
    TeamCreateBody,
    TeamJoinBody,
)
from backend.core.constants import BusinessElementName, PermissionName
from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.team.schemas import TeamWithMembersRead, TeamRead

router = APIRouter(
    prefix="/teams", tags=["Команды"], dependencies=[Depends(get_current_user)]
)


@router.get(
    path="/{team_id}/",
    response_model=TeamWithMembersRead,
    status_code=status.HTTP_200_OK,
    summary="Получить информацию о команде",
    responses={
        404: {"model": ErrorResponseSchema, "description": "Команда не найдена"},
    },
)
async def get_team(
    team_id: int,
    service: TeamServiceDepends,
):
    """
    Возвращает данные команды и список её участников.
    Если команда не существует - 404 Not Found
    """
    team = await service.get_team(team_id=team_id)
    return team


@router.post(
    path="/",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую команду",
    dependencies=[
        Depends(
            # Проверяет права на создание команды
            PermissionChecker(
                business_element=BusinessElementName.TEAMS,
                permission=PermissionName.CREATE,
            )
        )
    ],
    responses={
        400: {
            "model": ErrorResponseSchema,
            "description": "Команда с таким названием уже существует",
        },
    },
)
async def create_team(
    service: TeamServiceDepends,
    team_in: TeamCreateBody,
):
    """
    Создает новую пустую команду.
    Если такая уже есть - 400 Bad Request
    """
    team = await service.create_team(team_in)
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
    Код неправильный - 404 Not Found
    Попытка вступить повторно в свою текущую команду - 400 Bad Request
    """
    team = await service.join_team(user=current_user, invite_code=join_data.invite_code)
    return team

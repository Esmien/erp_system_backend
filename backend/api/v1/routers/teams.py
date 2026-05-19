from fastapi import APIRouter, HTTPException, status, Depends

from backend.api.dependencies.permissions import PermissionChecker, CurrentUserDepends
from backend.api.dependencies.teams import (
    TeamServiceDepends,
    TeamCreateBody,
    TeamJoinQuery,
)
from backend.core.constants import BusinessElementName, PermissionName
from backend.core.schemas.team import TeamWithMembersRead, TeamRead
from backend.exceptions import (
    TeamDoesNotExistsError,
    TeamAlreadyExistsError,
    UserAlreadyInTeamError,
)

router = APIRouter(prefix="/teams", tags=["Команды"])


@router.get(
    path="/{team_id}",
    response_model=TeamWithMembersRead,
    status_code=status.HTTP_200_OK,
    summary="Получить информацию о команде",
)
async def get_team(
    team_id: int,
    service: TeamServiceDepends,
):
    """
    Возвращает данные команды и список её участников.
    Если команда не существует - 404 Not Found
    """
    try:
        team = await service.get_team(team_id=team_id)
        return team
    except TeamDoesNotExistsError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена",
        )


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
)
async def create_team(
    service: TeamServiceDepends,
    team_in: TeamCreateBody,
):
    """
    Создает новую пустую команду.
    Если такая уже есть - 400 Bad Request
    """
    try:
        team = await service.create_team(team_in)
        return team
    except TeamAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Команда с таким названием уже существует",
        )


@router.post(
    path="/join",
    response_model=TeamRead,
    status_code=status.HTTP_200_OK,
    summary="Присоединиться к команде по коду",
)
async def join_team(
    join_data: TeamJoinQuery,
    service: TeamServiceDepends,
    current_user: CurrentUserDepends,
):
    """
    Привязывает пользователя к команде по 6-значному коду приглашения.
    Код неправильный - 404 Not Found
    Попытка вступить повторно в свою текущую команду - 400 Bad Request
    """
    try:
        team = await service.join_team(
            user=current_user, invite_code=join_data.invite_code
        )
        return team
    except TeamDoesNotExistsError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда с таким кодом не найдена",
        )
    except UserAlreadyInTeamError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже состоите в команде",
        )

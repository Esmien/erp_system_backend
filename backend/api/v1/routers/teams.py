from fastapi import APIRouter, HTTPException, status, Depends

from backend.api.dependencies.permissions import PermissionChecker
from backend.api.dependencies.teams import TeamServiceDepends
from backend.core.constants import BusinessElementName, PermissionName
from backend.core.schemas.team import TeamWithMembersRead, TeamRead, TeamCreate
from backend.exceptions import TeamDoesNotExistsError, TeamAlreadyExistsError

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
            PermissionChecker(
                business_element=BusinessElementName.TEAMS,
                permission=PermissionName.CREATE,
            )
        )
    ],
)
async def create_team(
    team_in: TeamCreate,
    service: TeamServiceDepends,
):
    """
    Создает новую пустую команду
    """
    try:
        team = await service.create_team(team_in)
        return team
    except TeamAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Команда с таким названием уже существует",
        )

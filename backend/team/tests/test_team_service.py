import pytest

from backend.core.enums import Action, BusinessElementName
from backend.exceptions import (
    AccessDeniedError,
    TeamAlreadyExistError,
    TeamDoesNotExistError,
    UserAlreadyInTeamError,
)
from backend.rbac.schemas import AccessContextDTO
from backend.team.schemas import TeamCreate, TeamRead, TeamWithMembersRead
from backend.user.schemas import UserDTO


def test_generate_invite_code(team_service):
    """Синхронный тест генерации кода"""
    code = team_service.generate_invite_code(length=6)
    assert len(code) == 6
    assert code.isalnum()
    assert code.isupper()


@pytest.mark.parametrize(
    "team_exists, expected_exception",
    [(True, None), (False, TeamDoesNotExistError)],
)
async def test_get_team(team_service, mock_uow, team_exists, expected_exception, mock_user):
    if team_exists:
        mock_uow.teams.get_by_id.return_value = TeamWithMembersRead(id=1, name="Test", invite_code="111111", members=[])
    else:
        mock_uow.teams.get_by_id.return_value = None

    if expected_exception:
        with pytest.raises(expected_exception):
            await team_service.get_team(team_id=1, user=mock_user)
    else:
        result = await team_service.get_team(team_id=1, user=mock_user)
        assert result.id == 1
        mock_uow.teams.get_by_id.assert_called_once_with(obj_id=1)
        # Проверяем RBAC
        team_service.rbac.enforce_permission.assert_awaited_once_with(
            user=mock_user,
            business_element_name=BusinessElementName.TEAMS,
            action=Action.READ,
            context=AccessContextDTO(is_participant=True),
            error_msg="Вы не можете посмотреть данные этой команды",
        )


async def test_get_team_access_denied(team_service, mock_uow, mock_user):
    team_service.rbac.enforce_permission.side_effect = AccessDeniedError("Недостаточно прав")
    with pytest.raises(AccessDeniedError):
        await team_service.get_team(team_id=1, user=mock_user)


@pytest.mark.parametrize("name_exists", [True, False])
async def test_create_team(team_service, mock_uow, name_exists, mock_user):
    team_in = TeamCreate(name="Test Team")
    mock_uow.teams.get_team_model_by_field.return_value = name_exists

    if name_exists:
        with pytest.raises(TeamAlreadyExistError):
            await team_service.create_team(team_in=team_in, user=mock_user)
    else:
        mock_uow.teams.create.return_value = TeamRead(id=1, name="Test Team", invite_code="FREE00")

        result = await team_service.create_team(team_in=team_in, user=mock_user)

        assert result.name == "Test Team"
        mock_uow.teams.create.assert_called_once()
        mock_uow.commit.assert_called_once()
        team_service.rbac.enforce_permission.assert_awaited_once_with(
            user=mock_user,
            business_element_name=BusinessElementName.TEAMS,
            context=None,
            action=Action.CREATE,
            error_msg="Недостаточно прав для создания команды",
        )


@pytest.mark.parametrize(
    "user_team_id, code_exists, expected_exception",
    [
        (1, True, UserAlreadyInTeamError),
        (None, False, TeamDoesNotExistError),
        (None, True, None),
    ],
)
async def test_join_team(team_service, mock_uow, user_team_id, code_exists, expected_exception):
    user = UserDTO(
        id=1,
        email="test@test.com",
        hashed_password="hash",
        name="Test",
        role_id=1,
        is_active=True,
        team_id=user_team_id,
    )

    if code_exists:
        mock_uow.teams.get_team_model_by_field.return_value = TeamRead(id=1, name="Team", invite_code="111111")
    else:
        mock_uow.teams.get_team_model_by_field.return_value = None

    if expected_exception:
        with pytest.raises(expected_exception):
            await team_service.join_team(user=user, invite_code="111111")
    else:
        result = await team_service.join_team(user=user, invite_code="111111")
        assert result.id == 1
        mock_uow.teams.add_user_to_team.assert_called_once_with(user_id=1, team_id=1)
        mock_uow.commit.assert_called_once()

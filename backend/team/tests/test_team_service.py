import pytest

from backend.team.schemas import TeamCreate, TeamRead, TeamWithMembersRead
from backend.user.schemas import UserDTO
from backend.exceptions import (
    TeamDoesNotExistsError,
    TeamAlreadyExistsError,
    UserAlreadyInTeamError,
)


def test_generate_invite_code(team_service):
    """Синхронный тест генерации кода"""
    code = team_service.generate_invite_code(length=6)

    assert len(code) == 6
    assert code.isalnum()
    assert code.isupper()


@pytest.mark.parametrize(
    "team_exists, expected_exception",
    [
        (True, None),
        (False, TeamDoesNotExistsError),
    ],
)
async def test_get_team(team_service, mock_uow, team_exists, expected_exception):
    if team_exists:
        mock_uow.teams.get_team_by_id.return_value = TeamWithMembersRead(
            id=1, name="Test", invite_code="111111", members=[]
        )
    else:
        mock_uow.teams.get_team_by_id.return_value = None

    if expected_exception:
        with pytest.raises(expected_exception):
            await team_service.get_team(1)
    else:
        result = await team_service.get_team(1)
        assert result.id == 1
        mock_uow.teams.get_team_by_id.assert_called_once_with(team_id=1)


@pytest.mark.parametrize("name_exists", [True, False])
async def test_create_team(team_service, mock_uow, name_exists):
    team_in = TeamCreate(name="Test Team")
    mock_uow.teams.check_team_name_exists.return_value = name_exists

    if name_exists:
        with pytest.raises(TeamAlreadyExistsError):
            await team_service.create_team(team_in)
    else:
        # Эмулируем работу while True: первый сгенерированный код занят, второй свободен
        mock_uow.teams.check_invite_code_exists.side_effect = [True, False]
        mock_uow.teams.create_team.return_value = TeamRead(
            id=1, name="Test Team", invite_code="FREE00"
        )

        result = await team_service.create_team(team_in)

        assert result.name == "Test Team"
        # Проверяем, что генератор сработал дважды из-за коллизии
        assert mock_uow.teams.check_invite_code_exists.call_count == 2
        mock_uow.teams.create_team.assert_called_once()
        mock_uow.commit.assert_called_once()


@pytest.mark.parametrize(
    "user_team_id, code_exists, expected_exception",
    [
        (1, True, UserAlreadyInTeamError),  # Юзер уже в команде
        (None, False, TeamDoesNotExistsError),  # Инвайт код не существует
        (None, True, None),  # Успешный джоин
    ],
)
async def test_join_team(
    team_service, mock_uow, user_team_id, code_exists, expected_exception
):
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
        mock_uow.teams.get_team_by_invite_code.return_value = TeamRead(
            id=1, name="Team", invite_code="111111"
        )
    else:
        mock_uow.teams.get_team_by_invite_code.return_value = None

    if expected_exception:
        with pytest.raises(expected_exception):
            await team_service.join_team(user, "111111")
    else:
        result = await team_service.join_team(user, "111111")

        assert result.id == 1
        mock_uow.teams.add_user_to_team.assert_called_once_with(user_id=1, team_id=1)
        mock_uow.commit.assert_called_once()

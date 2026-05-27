import pytest

from backend.team.schemas import TeamCreate


@pytest.mark.parametrize(
    "team_id, expected_exists",
    [
        (1, True),
        (999, False),
    ],
)
async def test_get_team_by_id(team_repo, team_id, expected_exists):
    result = await team_repo.get_team_by_id(team_id)

    if expected_exists:
        assert result is not None
        assert result.id == team_id
    else:
        assert result is None


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Dummy name", True),
        ("Non-existent Team", False),
    ],
)
async def test_check_team_name_exists(team_repo, name, expected):
    result = await team_repo.check_team_name_exists(name)
    assert result is expected


@pytest.mark.parametrize(
    "code, expected",
    [
        ("111111", True),
        ("000000", False),
    ],
)
async def test_check_invite_code_exists(team_repo, code, expected):
    result = await team_repo.check_invite_code_exists(code)
    assert result is expected


@pytest.mark.parametrize(
    "code, expected_exists",
    [
        ("111111", True),
        ("000000", False),
    ],
)
async def test_get_team_by_invite_code(team_repo, code, expected_exists):
    result = await team_repo.get_team_by_invite_code(code)

    if expected_exists:
        assert result.invite_code == code
    else:
        assert result is None


async def test_create_team(team_repo):
    team_in = TeamCreate(name="New Awesome Team", description="Test Description")
    code = "NEW123"

    result = await team_repo.create_team(team_in, code)

    assert result.id is not None
    assert result.name == "New Awesome Team"
    assert result.invite_code == code


@pytest.mark.parametrize(
    "user_id, team_id, expected_result",
    [
        (1, 1, True),  # Юзер есть, команда есть
        (999, 1, False),  # Юзера нет
        (1, 999, False),  # Команды нет
    ],
)
async def test_add_user_to_team(team_repo, user_id, team_id, expected_result):
    result = await team_repo.add_user_to_team(user_id=user_id, team_id=team_id)
    assert result is expected_result

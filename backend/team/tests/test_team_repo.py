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
    result = await team_repo.get_by_id(obj_id=team_id)

    if expected_exists:
        assert result is not None
        assert result.id == team_id
    else:
        assert result is None


@pytest.mark.parametrize(
    "field, value, should_exist",
    [
        # Проверяем поиск по имени
        ("name", "Dummy name", True),
        ("name", "Non-existent Team", False),
        ("invite_code", "111111", True),
        ("invite_code", "INVALID_INVITE", False),
    ],
)
async def test_get_team_model_by_field(team_repo, field, value, should_exist):
    result = await team_repo.get_team_model_by_field(field=field, value=value)

    if should_exist:
        # Проверяем, что команда нашлась
        assert result is not None
        # И что мы нашли именно то, что искали (через getattr достаем значение поля)
        assert getattr(result, field) == value
    else:
        # Если команды быть не должно, ожидаем строго None
        assert result is None


async def test_create_team(team_repo):
    team_in = TeamCreate(name="New Awesome Team", description="Test Description")
    code = "NEW123"

    result = await team_repo.create(**team_in.model_dump(), invite_code=code)

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

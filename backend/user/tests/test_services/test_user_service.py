import pytest

from backend.exceptions import UserDoesNotExistError
from backend.user.schemas import UserUpdate


@pytest.mark.parametrize(
    "update_data_dict, expected_to_call_repo",
    [
        (
            {
                "name": "New Name",
                "surname": "New Surname",
                "last_name": "New Last Name",
            },
            True,
        ),
        ({"name": "New Name", "surname": "New Surname"}, True),
        ({"last_name": "New Last Name"}, True),
        ({}, False),
    ],
)
async def test_update_profile(user_service, mock_uow, user_to_update, update_data_dict, expected_to_call_repo):
    update_schema = UserUpdate(**update_data_dict)
    mock_uow.users.update_user.return_value = user_to_update

    result = await user_service.update_profile(user=user_to_update, update_data=update_schema)

    if expected_to_call_repo:
        mock_uow.users.update_user.assert_called_once_with(user_id=user_to_update.id, update_dict=update_data_dict)
    else:
        mock_uow.users.update_user.assert_not_called()

    assert result == user_to_update


async def test_soft_delete_profile(user_service, mock_uow, user_to_update):
    result = await user_service.soft_delete_profile(user=user_to_update)

    mock_uow.users.soft_delete_user.assert_called_once_with(user_id=user_to_update.id)

    assert result is None


async def test_update_profile_not_found(user_service, mock_uow, user_to_update):
    update_schema = UserUpdate(name="New Name")
    mock_uow.users.update_user.return_value = None  # Имитируем, что юзер пропал из БД

    with pytest.raises(UserDoesNotExistError):
        await user_service.update_profile(user=user_to_update, update_data=update_schema)


async def test_soft_delete_profile_not_found(user_service, mock_uow, user_to_update):
    mock_uow.users.soft_delete_user.return_value = None

    with pytest.raises(UserDoesNotExistError):
        await user_service.soft_delete_profile(user=user_to_update)

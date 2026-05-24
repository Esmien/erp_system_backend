import pytest

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
async def test_update_profile(
    user_service, mock_repo, user_to_update, update_data_dict, expected_to_call_repo
):
    update_schema = UserUpdate(**update_data_dict)
    mock_repo.update_user.return_value = user_to_update

    result = await user_service.update_profile(
        user=user_to_update, update_data=update_schema
    )

    if expected_to_call_repo:
        mock_repo.update_user.assert_called_once_with(
            user_id=user_to_update.id, update_dict=update_data_dict
        )
    else:
        mock_repo.update_user.assert_not_called()

    assert result == user_to_update


async def test_soft_delete_profile(user_service, mock_repo, user_to_update):
    result = await user_service.soft_delete_profile(user=user_to_update)

    mock_repo.soft_delete_user.assert_called_once_with(user_id=user_to_update.id)

    assert result is None

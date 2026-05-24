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
    user_service, mock_repo, user_out, update_data_dict, expected_to_call_repo
):
    update_schema = UserUpdate(**update_data_dict)
    mock_repo.update_user.return_value = user_out

    result = await user_service.update_profile(user=user_out, update_data=update_schema)

    if expected_to_call_repo:
        mock_repo.update_user.assert_called_once_with(
            user=user_out, update_dict=update_data_dict
        )
    else:
        mock_repo.update_user.assert_not_called()

    assert result == user_out


async def test_soft_delete_profile(user_service, mock_repo, user_out):
    result = await user_service.soft_delete_profile(user=user_out)

    mock_repo.soft_delete_user.assert_called_once_with(user=user_out)

    assert result is None

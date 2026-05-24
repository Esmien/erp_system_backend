from unittest.mock import patch

import pytest

from backend.exceptions import InvalidPasswordError, UserDoesNotExistsError
from backend.user.models import User


@pytest.mark.parametrize(
    "email, plain_password, exc",
    [
        # Успешный кейс: юзер есть, пароль подходит, ошибки нет
        ("admin@admin.com", "valid_password", None),
        # Провал: юзер есть, но пароль не тот
        ("admin@admin.com", "invalid_password", InvalidPasswordError),
        # Провал: юзера вообще нет в базе
        ("invalid_username@user.com", "any_password", UserDoesNotExistsError),
    ],
)
@patch("backend.user.service.verify_password")
async def test_auth_check_creds(
    mock_verify_password, mock_repo, auth_service, email, plain_password, exc
):
    testing_user = None

    if exc == UserDoesNotExistsError:
        mock_repo.get_user.return_value = None
    else:
        testing_user = User(email=email, hashed_password="fake_hash")
        mock_repo.get_user.return_value = testing_user

    if exc == InvalidPasswordError:
        mock_verify_password.side_effect = InvalidPasswordError()
    else:
        # Очищаем side_effect на случай, если pytest переиспользует мок между итерациями
        mock_verify_password.side_effect = None

    if exc:
        with pytest.raises(exc):
            await auth_service.check_users_creds(email=email, password=plain_password)
    else:
        result = await auth_service.check_users_creds(
            email=email, password=plain_password
        )

        assert result == testing_user

        mock_verify_password.assert_called_once_with(
            plain_password=plain_password, hashed_password="fake_hash"
        )

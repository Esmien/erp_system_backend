from unittest.mock import patch

import pytest

from backend.exceptions import (
    InvalidPasswordError,
    UserDoesNotExistsError,
    UserNotActiveError,
    UserAlreadyActiveError,
)
from backend.user.models import User
from backend.user.schemas import UserDTO, Token


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
    mock_verify_password, mock_uow, auth_service, email, plain_password, exc
):
    testing_user = None

    if exc == UserDoesNotExistsError:
        mock_uow.auth.get_user.return_value = None
    else:
        testing_user = User(email=email, hashed_password="fake_hash")
        mock_uow.auth.get_user.return_value = testing_user

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


@pytest.mark.parametrize(
    "is_active, uow_returns_user, expected_exc",
    [
        (True, None, UserAlreadyActiveError),  # Уже активен
        (False, False, UserDoesNotExistsError),  # UoW ничего не вернул
        (False, True, None),  # Успешная активация
    ],
)
async def test_activate_user(
    auth_service, mock_uow, is_active, uow_returns_user, expected_exc
):
    user = UserDTO(
        id=1,
        email="test@test.com",
        hashed_password="hash",
        name="Test",
        role_id=1,
        is_active=is_active,
    )

    if uow_returns_user:
        mock_uow.auth.activate_user.return_value = user
    else:
        mock_uow.auth.activate_user.return_value = None

    if expected_exc:
        with pytest.raises(expected_exc):
            await auth_service.activate_user(user)
    else:
        res = await auth_service.activate_user(user)
        assert res == user
        mock_uow.commit.assert_called_once()


@pytest.mark.parametrize(
    "is_active, expected_exc",
    [
        (False, UserNotActiveError),
        (True, None),
    ],
)
def test_get_auth_token(auth_service, is_active, expected_exc):
    user = UserDTO(
        id=1,
        email="test@test.com",
        hashed_password="hash",
        name="Test",
        role_id=1,
        is_active=is_active,
    )
    if expected_exc:
        with pytest.raises(expected_exc):
            auth_service.get_auth_token(user)
    else:
        token = auth_service.get_auth_token(user)
        assert isinstance(token, Token)
        assert token.token_type == "bearer"
        assert isinstance(token.access_token, str)


@pytest.mark.parametrize(
    "uow_returns_user, is_active, expected_exc",
    [
        (False, False, UserDoesNotExistsError),  # Не найден
        (True, False, UserNotActiveError),  # Найден, но деактивирован
        (True, True, None),  # Успех
    ],
)
async def test_get_active_user_by_id(
    auth_service, mock_uow, uow_returns_user, is_active, expected_exc
):
    if uow_returns_user:
        user = UserDTO(
            id=1,
            email="test@test.com",
            hashed_password="hash",
            name="Test",
            role_id=1,
            is_active=is_active,
        )
        mock_uow.auth.get_user_and_role_by_user_id.return_value = user
    else:
        mock_uow.auth.get_user_and_role_by_user_id.return_value = None
        user = None

    if expected_exc:
        with pytest.raises(expected_exc):
            await auth_service.get_active_user_by_id(1)
    else:
        res = await auth_service.get_active_user_by_id(1)
        assert res == user

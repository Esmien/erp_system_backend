from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt
import pytest

from backend.exceptions import (
    BadCredentialsError,
    InvalidPasswordError,
    UserAlreadyActiveError,
    UserDoesNotExistError,
    UserNotActiveError,
)
from backend.user.models import User
from backend.user.schemas import Token, UserDTO


@pytest.mark.parametrize(
    "email, plain_password, exc",
    [
        # Успешный кейс: юзер есть, пароль подходит, ошибки нет
        ("admin@admin.com", "valid_password", None),
        # Провал: юзер есть, но пароль не тот
        ("admin@admin.com", "invalid_password", BadCredentialsError),
        # Провал: юзера вообще нет в базе
        ("invalid_username@user.com", "any_password", BadCredentialsError),
    ],
)
@patch("backend.user.service.verify_password")
async def test_auth_check_creds(mock_verify_password, mock_uow, auth_service, email, plain_password, exc):
    testing_user = None

    if exc == BadCredentialsError:
        mock_uow.auth.get_user.return_value = None
    else:
        testing_user = User(email=email, hashed_password="fake_hash")
        mock_uow.auth.get_user.return_value = testing_user

    if exc == BadCredentialsError:
        mock_verify_password.side_effect = InvalidPasswordError()
    else:
        # Очищаем side_effect на случай, если pytest переиспользует мок между итерациями
        mock_verify_password.side_effect = None

    if exc:
        with pytest.raises(exc):
            await auth_service.check_users_creds(email=email, password=plain_password)
    else:
        result = await auth_service.check_users_creds(email=email, password=plain_password)

        assert result == testing_user

        mock_verify_password.assert_called_once_with(plain_password=plain_password, hashed_password="fake_hash")


@pytest.mark.parametrize(
    "is_active, uow_returns_user, expected_exc",
    [
        (True, None, UserAlreadyActiveError),  # Уже активен
        (False, False, UserDoesNotExistError),  # UoW ничего не вернул
        (False, True, None),  # Успешная активация
    ],
)
async def test_activate_user(auth_service, mock_uow, is_active, uow_returns_user, expected_exc):
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
        (False, False, UserDoesNotExistError),  # Не найден
        (True, False, UserNotActiveError),  # Найден, но деактивирован
        (True, True, None),  # Успех
    ],
)
async def test_get_active_user_by_id(auth_service, mock_uow, uow_returns_user, is_active, expected_exc):
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


# Константы для мока настроек
TEST_SECRET = "super_secret_test_key_that_is_at_least_32_bytes_long"
TEST_ALGO = "HS256"


@patch("backend.user.service.settings")
async def test_logout_success_adds_to_blacklist(mock_settings, mock_redis, auth_service):
    """Тест: валидный токен успешно добавляется в Redis с правильным TTL"""
    # 1. Подготавливаем моки
    mock_settings.security.SECRET_KEY = TEST_SECRET
    mock_settings.security.ALGORITHM = TEST_ALGO

    # 2. Генерируем тестовый токен, который истекает через 15 минут
    exp_time = datetime.now(tz=UTC) + timedelta(minutes=15)
    test_jti = "test-uuid-12345"

    payload = {
        "sub": "1",
        "jti": test_jti,
        "exp": exp_time,
    }
    valid_token = jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGO)

    # 3. Вызываем тестируемый метод
    await auth_service.logout(token=valid_token, redis=mock_redis)

    # 4. Проверки
    mock_redis.setex.assert_called_once()

    # Достаем аргументы, с которыми был вызван redis.setex
    call_args = mock_redis.setex.call_args.args
    called_key = call_args[0]
    called_ttl = call_args[1]
    called_value = call_args[2]

    assert called_key == f"jwt:blacklist:{test_jti}"
    assert called_value == "revoked"
    # TTL должен быть около 900 секунд (15 минут), даем погрешность в пару секунд на выполнение теста
    assert 895 < called_ttl <= 900


@patch("backend.user.service.settings")
async def test_logout_invalid_token_ignored(mock_settings, mock_redis, auth_service):
    """Тест: при попытке логаута с невалидным токеном Redis не вызывается"""
    # 1. Подготавливаем моки
    mock_settings.security.SECRET_KEY = TEST_SECRET
    mock_settings.security.ALGORITHM = TEST_ALGO

    invalid_token = "some.invalid.jwt_token"

    # 2. Вызываем метод
    await auth_service.logout(token=invalid_token, redis=mock_redis)

    # 3. Проверяем, что метод не упал с ошибкой и НЕ трогал Redis
    mock_redis.setex.assert_not_called()

import pytest
from unittest.mock import patch
import jwt
from fastapi import HTTPException

from backend.api.dependencies.permissions import get_current_user, PermissionChecker
from backend.core.constants import BusinessElementName, PermissionName
from backend.exceptions import UserDoesNotExistsError, UserNotActiveError
from backend.user.schemas import UserDTO

# Секреты для тестов
TEST_SECRET = "super_secret_test_key_that_is_at_least_32_bytes_long"
TEST_ALGO = "HS256"


@pytest.mark.parametrize(
    "token_payload, expected_exception",
    [
        ({"sub": "1"}, None),  # Успешный кейс
        ({}, HTTPException),  # Нет sub в токене (401)
        (None, HTTPException),  # Невалидный токен (ошибка декодирования)
    ],
)
@patch("backend.api.dependencies.permissions.settings")
async def test_get_current_user(
    mock_settings, auth_service_mock, token_payload, expected_exception
):
    mock_settings.security.SECRET_KEY = TEST_SECRET
    mock_settings.security.ALGORITHM = TEST_ALGO

    # Настраиваем токен
    if token_payload is None:
        token = "invalid_token_string"
    else:
        token = jwt.encode(token_payload, TEST_SECRET, algorithm=TEST_ALGO)

    # Настраиваем мок сервиса для успешного сценария
    auth_service_mock.get_active_user_by_id.return_value = UserDTO(
        id=1,
        email="test@test.com",
        hashed_password="hash",
        name="Test",
        role_id=1,
        is_active=True,
    )

    if expected_exception:
        with pytest.raises(expected_exception) as exc_info:
            await get_current_user(auth_service=auth_service_mock, token=token)
        assert exc_info.value.status_code == 401
    else:
        user = await get_current_user(auth_service=auth_service_mock, token=token)
        assert user.id == 1
        auth_service_mock.get_active_user_by_id.assert_called_once_with(user_id=1)


@pytest.mark.parametrize(
    "service_exception", [UserDoesNotExistsError, UserNotActiveError]
)
@patch("backend.api.dependencies.permissions.settings")
async def test_get_current_user_service_errors(
    mock_settings, auth_service_mock, valid_token, service_exception
):
    mock_settings.security.SECRET_KEY = TEST_SECRET
    mock_settings.security.ALGORITHM = TEST_ALGO

    auth_service_mock.get_active_user_by_id.side_effect = service_exception()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(auth_service=auth_service_mock, token=valid_token)

    assert exc_info.value.status_code == 401


@pytest.mark.parametrize(
    "has_access, expected_exception",
    [
        (True, None),  # Права есть
        (False, HTTPException),  # Прав нет (403)
    ],
)
async def test_permission_checker(rbac_service_mock, has_access, expected_exception):
    rbac_service_mock.check_permission.return_value = has_access

    checker = PermissionChecker(
        business_element=BusinessElementName.TEAMS, permission=PermissionName.CREATE
    )

    user = UserDTO(
        id=1,
        email="test@test.com",
        hashed_password="hash",
        name="Test",
        role_id=2,
        is_active=True,
    )

    if expected_exception:
        with pytest.raises(expected_exception) as exc_info:
            await checker(user=user, rbac_service=rbac_service_mock)
        assert exc_info.value.status_code == 403
    else:
        result_user = await checker(user=user, rbac_service=rbac_service_mock)
        assert result_user == user

    rbac_service_mock.check_permission.assert_called_once_with(
        role_id=2,
        element_name=BusinessElementName.TEAMS,
        permission=PermissionName.CREATE,
    )

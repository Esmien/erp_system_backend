import pytest

from backend.exceptions import BadCredentialsError, RoleDoesNotExistError, UserExistsError


@pytest.mark.parametrize("exc", [None, UserExistsError, RoleDoesNotExistError])
async def test_register_cases(mock_settings, mock_redis, user_in, user_out, mock_uow, register_service, exc):
    mock_redis.get.return_value = "000000"
    # 1. Мокаем поиск роли
    if exc == RoleDoesNotExistError:
        mock_uow.register.get_role_id.return_value = None
    else:
        mock_uow.register.get_role_id.return_value = 1

    # 2. Мокаем регистрацию (если вернулся None — значит был конфликт email)
    if exc == UserExistsError:
        mock_uow.register.register_user.return_value = None
    else:
        mock_uow.register.register_user.return_value = user_out

    # 3. Проверяем поведение сервиса
    if exc:
        with pytest.raises(exc):
            await register_service.register_user(user_in=user_in, redis=mock_redis)
    else:
        result = await register_service.register_user(user_in=user_in, redis=mock_redis)
        redis_reg_code_key = mock_settings.redis_keys.key_reg_code(code=user_in.register_code)
        assert result == user_out
        # Если всё прошло успешно, сервис должен был закоммитить транзакцию
        mock_uow.commit.assert_called_once()
        mock_redis.delete.assert_called_once_with(redis_reg_code_key)


async def test_register_invalid_code(mock_redis, user_in, register_service):
    # Учим мок Redis имитировать отсутствие кода (код неверный или протух)
    mock_redis.get.return_value = None

    with pytest.raises(BadCredentialsError) as exc_info:
        await register_service.register_user(user_in=user_in, redis=mock_redis)

    assert str(exc_info.value) == "Код регистрации недействителен или уже был использован"

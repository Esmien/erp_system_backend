import pytest

from backend.exceptions import RoleDoesNotExistError, UserExistsError


@pytest.mark.parametrize("exc", [None, UserExistsError, RoleDoesNotExistError])
async def test_register_cases(user_in, user_out, mock_uow, register_service, exc):
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
            await register_service.register_user(user_in=user_in)
    else:
        result = await register_service.register_user(user_in=user_in)
        assert result == user_out
        # Если всё прошло успешно, сервис должен был закоммитить транзакцию
        mock_uow.commit.assert_called_once()

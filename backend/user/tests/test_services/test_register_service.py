import pytest

from backend.exceptions import UserExistsError, RoleDoesNotExistError


@pytest.mark.parametrize("exc", [None, UserExistsError, RoleDoesNotExistError])
async def test_register_cases(user_in, user_out, mock_uow, register_service, exc):

    if exc == UserExistsError:
        mock_uow.register.check_user_exists.return_value = True
    else:
        mock_uow.register.check_user_exists.return_value = False

    if exc == RoleDoesNotExistError:
        mock_uow.register.get_role_id.return_value = None
    else:
        mock_uow.register.get_role_id.return_value = 1

    mock_uow.register.register_user.return_value = user_out

    if exc:
        with pytest.raises(exc):
            await register_service.register_user(user_in=user_in)
    else:
        result = await register_service.register_user(user_in=user_in)
        assert result == user_out

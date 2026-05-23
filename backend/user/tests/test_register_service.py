from unittest.mock import MagicMock, AsyncMock

import pytest

from backend.core.database import load_all_models
from backend.exceptions import UserExistsError, RoleDoesNotExistsError
from backend.user.service import RegisterService


load_all_models()


async def test_register_success(user_in, user_out):

    repo = MagicMock()
    repo.check_user_exists = AsyncMock(return_value=False)
    repo.get_role_id = AsyncMock(return_value=1)
    repo.register_user = AsyncMock(return_value=user_out)
    service = RegisterService(repo=repo)

    result = await service.register_user(user_in=user_in)

    assert result == user_out


async def test_register_already_exists(user_in):
    repo = MagicMock()
    repo.check_user_exists = AsyncMock(return_value=True)

    service = RegisterService(repo=repo)

    with pytest.raises(UserExistsError):
        await service.register_user(user_in=user_in)


async def test_register_role_not_found(user_in):
    repo = MagicMock()
    repo.check_user_exists = AsyncMock(return_value=False)
    repo.get_role_id = AsyncMock(return_value=None)
    service = RegisterService(repo=repo)

    with pytest.raises(RoleDoesNotExistsError):
        await service.register_user(user_in=user_in)

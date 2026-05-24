import asyncio
from unittest.mock import AsyncMock

import pytest

from backend.core.security import get_password_hash
from backend.user.models import User
from backend.user.schemas import UserRegister
from backend.user.service import RegisterService, AuthService

HASHED_PASSWORD = asyncio.run(get_password_hash("test"))


@pytest.fixture
def user_in():
    return UserRegister(
        email="test@test.com",
        password="test",
        repeat_password="test",
        name="Test",
        surname="Test_1",
        last_name="Test_2",
    )


@pytest.fixture
def user_out():
    return User(
        id=1,
        email="test@test.com",
        hashed_password=HASHED_PASSWORD,
        name="Test",
        surname="Test_1",
        last_name="Test_2",
        role_id=1,
        is_active=True,
    )


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def register_service(mock_repo):
    return RegisterService(repo=mock_repo)


@pytest.fixture
def auth_service(mock_repo):
    return AuthService(repo=mock_repo)

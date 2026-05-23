import asyncio

import pytest

from backend.core.security import get_password_hash
from backend.user.models import User
from backend.user.schemas import UserRegister

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

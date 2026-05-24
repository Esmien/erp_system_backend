import asyncio
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from backend.core.security import get_password_hash
from backend.user.repository import RegisterRepository, AuthRepository, UserRepository
from backend.user.schemas import UserRegister, UserDTO
from backend.user.service import RegisterService, AuthService, UserService
from tests.fixtures.init_db_fixtures import test_async_session_maker


# pytest_plugins = [
#     "tests.fixtures.init_db_fixtures",
# ]


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
    return UserDTO(
        id=5,
        email="test@test.com",
        hashed_password=HASHED_PASSWORD,
        name="Test",
        surname="Test_1",
        last_name="Test_2",
        role_id=1,
        is_active=True,
    )


@pytest.fixture
def user_to_update():
    return UserDTO(
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


@pytest.fixture
def user_service(mock_repo):
    return UserService(repo=mock_repo)


@pytest_asyncio.fixture
async def db_session():
    async with test_async_session_maker() as session:
        yield session


@pytest.fixture
def register_repo(db_session):
    return RegisterRepository(session=db_session)


@pytest.fixture
def auth_repo(db_session):
    return AuthRepository(session=db_session)


@pytest.fixture
def user_repo(db_session):
    return UserRepository(session=db_session)
